from sqlalchemy import Boolean, Column, Enum, Integer, ForeignKey, String, Text, DateTime, UniqueConstraint
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

    __table_args__ = (
        UniqueConstraint('application_id', 'review_officer_id', name='uq_application_officer'),
    ) 
    
    def __repr__(self):
        return f"<ApplicationReview for App {self.application_id} by Officer {self.review_officer_id}>"
    
    
class ApplicationReviewStep(Base):
    __tablename__ = "application_review_steps"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("permit_applications.id"))
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    step_name = Column(String)  # e.g., "Zoning Compliance", "Documents"

    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    flagged = Column(Boolean, default=False)
    flag_reason = Column(Text, nullable=True)
    flagged_at = Column(DateTime, nullable=True)

    application = relationship("PermitApplication", back_populates="review_steps")
    reviewer = relationship("User", back_populates="review_steps")

    __table_args__ = (
        UniqueConstraint("application_id", "reviewer_id", "step_name"),
    )

