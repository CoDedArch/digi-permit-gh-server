from sqlalchemy import Column, Enum, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
from app.core.constants import ReviewStatus, ReviewOutcome

class ApplicationReview(Base, TimestampMixin):
    __tablename__ = 'application_reviews'
    
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('permit_applications.id'), nullable=False)
    review_officer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING)
    outcome = Column(Enum(ReviewOutcome))
    comments = Column(Text)
    requested_additional_info = Column(Text)
    deadline = Column(DateTime)
    
    # Relationships
    application = relationship("PermitApplication", back_populates="reviews")
    review_officer = relationship("User", back_populates="assigned_reviews")
    
    def __repr__(self):
        return f"<ApplicationReview for App {self.application_id} by Officer {self.review_officer_id}>"