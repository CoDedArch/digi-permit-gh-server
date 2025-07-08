from sqlalchemy import Column, Enum, Integer,Boolean, ForeignKey, Text, DateTime
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
    # Relationships
    application = relationship("PermitApplication", back_populates="inspections")
    inspection_officer = relationship(
    "User",
    back_populates="assigned_inspections",
    foreign_keys=[inspection_officer_id]
    )
    applicant = relationship("User", foreign_keys=[applicant_id])
    mmda = relationship("MMDA")

    
    def __repr__(self):
        return f"<Inspection {self.inspection_type.value} for App {self.application_id}>"