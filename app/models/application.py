from sqlalchemy import Column, String, Enum, Integer, ForeignKey, Text, Float, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
from app.core.constants import PermitType, ApplicationStatus


class PermitApplication(Base, TimestampMixin):
    __tablename__ = 'permit_applications'
    
    id = Column(Integer, primary_key=True)
    application_number = Column(String(50), unique=True, nullable=False)
    applicant_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    permit_type = Column(Enum(PermitType), nullable=False)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.DRAFT)
    project_name = Column(String(255), nullable=False)
    project_description = Column(Text)
    project_address = Column(String(255), nullable=False)
    estimated_cost = Column(Float)
    construction_area = Column(Float)  # in square meters
    expected_start_date = Column(DateTime)
    expected_end_date = Column(DateTime)
    
    # Relationships
    applicant = relationship("User", back_populates="applications")
    documents = relationship("ApplicationDocument", back_populates="application")
    reviews = relationship("ApplicationReview", back_populates="application")
    inspections = relationship("Inspection", back_populates="application")
    payments = relationship("Payment", back_populates="application")
    
    def __repr__(self):
        return f"<PermitApplication {self.application_number}>"