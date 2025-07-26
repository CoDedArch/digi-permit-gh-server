from sqlalchemy import Column, Enum, Integer,Boolean, ForeignKey, String, Text, DateTime, func
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
from app.core.constants import InspectionType, InspectionStatus, InspectionOutcome


class Inspection(Base, TimestampMixin):
    __tablename__ = 'inspections'
    
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('permit_applications.id'), nullable=False)
    inspection_officer_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    applicant_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    mmda_id = Column(Integer, ForeignKey('mmdas.id'), nullable=False)
    inspection_type = Column(Enum(InspectionType), nullable=False)
    status = Column(Enum(InspectionStatus), default=InspectionStatus.PENDING)
    outcome = Column(Enum(InspectionOutcome))
    scheduled_date = Column(DateTime)
    actual_date = Column(DateTime)
    findings = Column(Text)
    recommendations = Column(Text)
    violations_found = Column(Text)
    notes = Column(Text)
    is_reinspection = Column(Boolean, default=False)
    assigned_officer_id = Column(Integer, ForeignKey('users.id'))
    special_instructions = Column(Text)
    # Relationships
    application = relationship("PermitApplication", back_populates="inspections")
    inspection_officer = relationship( 
    "User",
    back_populates="assigned_inspections",
    foreign_keys=[inspection_officer_id]
    )
    applicant = relationship("User", foreign_keys=[applicant_id])
    photos = relationship("InspectionPhoto", back_populates="inspection", cascade="all, delete-orphan")
    mmda = relationship("MMDA")

    
    def __repr__(self):
        return f"<Inspection {self.inspection_type.value} for App {self.application_id}>"


class InspectionPhoto(Base):
    __tablename__ = 'inspection_photos'
    
    id = Column(Integer, primary_key=True)
    inspection_id = Column(Integer, ForeignKey('inspections.id'), nullable=False)
    file_path = Column(String(512), nullable=False)
    caption = Column(String(255))  # Optional caption for the photo
    uploaded_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Who uploaded the photo
    uploaded_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    inspection = relationship("Inspection", back_populates="photos")
    uploaded_by = relationship("User")
    
    def __repr__(self):
        return f"<InspectionPhoto {self.id} for Inspection {self.inspection_id}>"