from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Column, ForeignKey, String, JSON, Integer, Float, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.core.constants import ZoneType


class ZoningDistrict(Base):
    __tablename__ = "zoning_districts"
    
    id = Column(Integer, primary_key=True)
    code = Column(ENUM(ZoneType), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    max_height = Column(Float)  # in meters
    max_coverage = Column(Float)  # as decimal (0.45 = 45%)
    min_plot_size = Column(Float)  # in m²
    color_code = Column(String(50))
    density = Column(String(50))  # e.g., "10-15 dwellings/ha"
    parking_requirement = Column(String(100))
    setbacks = Column(String(150))
    special_notes = Column(Text)
    spatial_data = Column(Geometry("POLYGON", srid=4326))
    population_served = Column(String(100))  # e.g., "Up to 5,000"
    buffer_zones = Column(String(150))
    
    # New relationships
    permitted_uses = relationship("ZoningPermittedUse", back_populates="zoning_district", cascade="all, delete-orphan")
    prohibited_uses = relationship("ZoningProhibitedUse", back_populates="zoning_district", cascade="all, delete-orphan")


class ZoningPermittedUse(Base):
    __tablename__ = "zoning_permitted_uses"

    id = Column(Integer, primary_key=True)
    zoning_district_id = Column(Integer, ForeignKey("zoning_districts.id", ondelete="CASCADE"))
    use = Column(String(255), nullable=False)

    requires_epa_approval = Column(Boolean, default=False)
    requires_heritage_review = Column(Boolean, default=False)
    requires_traffic_study = Column(Boolean, default=False)

    zoning_district = relationship("ZoningDistrict", back_populates="permitted_uses")

    required_documents = relationship(
        "ZoningUseDocumentRequirement",
        back_populates="zoning_use",
        cascade="all, delete-orphan"
    )

class ZoningUseDocumentRequirement(Base):
    __tablename__ = "zoning_use_document_requirements"

    id = Column(Integer, primary_key=True)
    zoning_use_id = Column(Integer, ForeignKey("zoning_permitted_uses.id", ondelete="CASCADE"))
    document_type_id = Column(Integer, ForeignKey("document_types.id", ondelete="CASCADE"))
    is_mandatory = Column(Boolean, default=True)
    phase = Column(String(50))  # e.g. "application", "review", "approval"
    notes = Column(String)

    zoning_use = relationship("ZoningPermittedUse", back_populates="required_documents")
    document_type = relationship("DocumentTypeModel")


class ZoningProhibitedUse(Base):
    __tablename__ = "zoning_prohibited_uses"

    id = Column(Integer, primary_key=True)
    zoning_district_id = Column(Integer, ForeignKey("zoning_districts.id", ondelete="CASCADE"))
    use = Column(String(255), nullable=False)

    zoning_district = relationship("ZoningDistrict", back_populates="prohibited_uses")
