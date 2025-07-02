from datetime import datetime
from enum import Enum
from geoalchemy2 import Geometry
from sqlalchemy import Column, Index, Integer, String, Text, Float, DateTime, ForeignKey, Enum as SQLEnum, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base
from app.core.constants import ApplicationStatus
from app.models.zoning import application_site_conditions


class PermitApplication(Base):
    __tablename__ = 'permit_applications'
    
    id = Column(Integer, primary_key=True)
    application_number = Column(String(50), unique=True, nullable=False, index=True)
    mmda_id = Column(Integer, ForeignKey('mmdas.id'), nullable=False)
    architect_id = Column(Integer, ForeignKey("professionals.id", ondelete="SET NULL"))
    applicant_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    permit_type_id = Column(String(50), ForeignKey('permit_types.id'), nullable=False)
    zoning_district_id = Column(Integer, ForeignKey("zoning_districts.id"), nullable=True)
    zoning_use_id = Column(Integer, ForeignKey("zoning_permitted_uses.id"), nullable=True)
    drainage_type_id = Column(Integer, ForeignKey("drainage_types.id"))
    status = Column(SQLEnum(ApplicationStatus), default=ApplicationStatus.DRAFT, nullable=False, index=True)
    project_name = Column(String(255), nullable=False)
    project_description = Column(Text)
    parking_spaces = Column(Integer)
    setbacks = Column(JSONB)
    floor_areas = Column(JSONB)
    site_conditions = Column(JSONB)  # {"existing_structures": "block wall", "public_services": "storm drain nearby"}
    previous_land_use_id = Column(Integer, ForeignKey("previous_land_uses.id", ondelete="SET NULL"))
    drainage_type = Column(String(100))
    project_address = Column(String(255), nullable=False)
    parcel_number = Column(String(50))  # Important for property identification
    estimated_cost = Column(Float)
    construction_area = Column(Float)  # in square meters
    expected_start_date = Column(DateTime)
    expected_end_date = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    submitted_at = Column(DateTime)
    approved_at = Column(DateTime)

    # GIS SPATIAL FIELDS
    latitude = Column(Float, comment="Decimal degrees (WGS84)")
    longitude = Column(Float, comment="Decimal degrees (WGS84)")
    parcel_geometry = Column(
        Geometry('POLYGON', srid=4326), 
        comment="Property boundary in GeoJSON format"
    )
    project_location = Column(
        Geometry('POINT', srid=4326),
        index=True,
        comment="Specific project coordinates"
    )
    gis_metadata = Column(
        JSONB,
        comment="Additional spatial attributes like elevation, zoning codes, etc."
    )

    # Relationships
    zoning_use = relationship("ZoningPermittedUse")
    drainage_type = relationship("DrainageType", back_populates="applications")
    zoning_district = relationship("ZoningDistrict")
    site_conditions = relationship("SiteCondition", secondary=application_site_conditions, back_populates="applications")
    architect = relationship("ProfessionalInCharge", back_populates="applications")
    mmda = relationship("MMDA", back_populates="permit_applications")
    applicant = relationship("User", back_populates="applications")
    permit_type = relationship("PermitTypeModel", back_populates="applications")
    documents = relationship(
        "ApplicationDocument", 
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ApplicationDocument.uploaded_at.desc()"
    )
    reviews = relationship(
        "ApplicationReview",
        back_populates="application",
        order_by="ApplicationReview.created_at.desc()"
    )
    inspections = relationship(
        "Inspection",
        back_populates="application",
        order_by="Inspection.scheduled_date.desc()"
    )
    payments = relationship(
        "Payment",
        back_populates="application",
        order_by="Payment.payment_date.desc()"
    )
    status_history = relationship(
        "ApplicationStatusHistory",
        back_populates="application",
        order_by="ApplicationStatusHistory.changed_at.desc()"
    )
    
    # Indexes
    __table_args__ = (
        Index('ix_permit_applications_applicant', 'applicant_id'),
        Index('ix_permit_applications_created', 'created_at'),
    )
    
    @validates('estimated_cost')
    def validate_estimated_cost(self, key, cost):
        if cost is not None and cost < 0:
            raise ValueError("Estimated cost cannot be negative")
        return cost
    
    @validates('latitude')
    def validate_latitude(self, key, value):
        if value is not None and (value < -90 or value > 90):
            raise ValueError("Latitude must be between -90 and 90")
        return value
    
    @validates('longitude')
    def validate_longitude(self, key, value):
        if value is not None and (value < -180 or value > 180):
            raise ValueError("Longitude must be between -180 and 180")
        return value
    
    @validates('construction_area')
    def validate_construction_area(self, key, area):
        if area is not None and area <= 0:
            raise ValueError("Construction area must be positive")
        return area
    
    @validates('expected_start_date', 'expected_end_date')
    def validate_dates(self, key, date):
        if date is not None and date < datetime.now():
            raise ValueError("Date cannot be in the past")
        return date
    
    def is_submittable(self):
        """Check if application meets minimum requirements for submission"""
        required_docs = [doc for doc in self.documents if doc.is_required]
        return (
            self.status == ApplicationStatus.DRAFT and
            len(required_docs) >= self.permit_type.min_required_documents
        )
    
    # GIS UTILITY METHODS
    def get_geojson_point(self):
        """Returns project location as GeoJSON feature"""
        if not self.longitude or not self.latitude:
            return None
            
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude]
            },
            "properties": {
                "application_number": self.application_number,
                "status": self.status.value
            }
        }
    
    def calculate_area(self, db: AsyncSession):
        """Returns parcel area in square meters"""
        if self.parcel_geometry:
            # This would be executed as a database function
            return db.scalar(
                select([func.ST_Area(self.parcel_geometry)])
            )
        return None
    
    # ======================
    # Spatial Query Examples
    # ======================
    @classmethod
    async def find_nearby(cls, db: AsyncSession, point: tuple, distance_meters: int):
        """Find applications within radius of a point (lng, lat)"""
        from geoalchemy2.functions import ST_DWithin, ST_MakePoint
        
        return await db.execute(
            select(cls)
            .where(
                ST_DWithin(
                    cls.project_location,
                    ST_MakePoint(point[0], point[1]),
                    distance_meters
                )
            )
        )
    
    
    def __repr__(self):
        return f"<PermitApplication {self.application_number} ({self.status})>"

class ApplicationStatusHistory(Base):
    __tablename__ = 'application_status_history'
    
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('permit_applications.id'))
    from_status = Column(SQLEnum(ApplicationStatus))
    to_status = Column(SQLEnum(ApplicationStatus))
    changed_by_id = Column(Integer, ForeignKey('users.id'))
    notes = Column(Text)
    changed_at = Column(DateTime, server_default=func.now())
    
    application = relationship("PermitApplication", back_populates="status_history")
    changed_by = relationship("User")