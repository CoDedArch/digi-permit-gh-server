from sqlalchemy import Column, String, Integer, Enum, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
from app.core.constants import UserRole, VerificationStage
import enum

class UnverifiedUser(Base, TimestampMixin):
    __tablename__ = 'unverified_users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    phone = Column(String(20), unique=True)
    otp_secret = Column(String(100), nullable=False)
    otp_expires = Column(DateTime, nullable=False)
    verification_channel = Column(String(10), nullable=False)  # 'email' or 'sms'
    verification_attempts = Column(Integer, default=0)
    is_locked = Column(Boolean, default=False)
    lock_expires = Column(DateTime)
    
    def __repr__(self):
        return f"<UnverifiedUser {self.email or self.phone}>"

class User(Base, TimestampMixin):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    other_name = Column(String(100))
    phone = Column(String(20), unique=True, nullable=False)
    alt_phone = Column(String(20), unique=True)
    is_active = Column(Boolean, default=False)  # Disabled until Ghana Card verification
    preferred_verification = Column(String(10), default='email')
    role = Column(Enum(UserRole), nullable=False, default=UserRole.APPLICANT)
    verification_stage = Column(Enum(VerificationStage), 
                              default=VerificationStage.OTP_PENDING)  # Tracks verification progress
    
    # Relationships
    profile = relationship("UserProfile", uselist=False, back_populates="user")
    documents = relationship("UserDocument", back_populates="user")
    applications = relationship("PermitApplication", back_populates="applicant")
    assigned_inspections = relationship(
    "Inspection",
    back_populates="inspection_officer",
    foreign_keys="Inspection.inspection_officer_id"
    )
    assigned_reviews = relationship(
    "ApplicationReview",
    back_populates="review_officer",
    foreign_keys="ApplicationReview.review_officer_id"
    )



    @property
    def can_apply_for_permit(self) -> bool:
        """Check if user has completed all verification steps"""
        return (self.is_active and 
                self.verification_stage == VerificationStage.FULLY_VERIFIED and
                all(doc.verification_status == "approved" 
                    for doc in self.documents 
                    if doc.document_type in ["GHANA_CARD_FRONT", "GHANA_CARD_BACK"]))
    
    def __repr__(self):
        return f"<User {self.email} ({self.role.value})>"

class UserProfile(Base, TimestampMixin):
    __tablename__ = 'user_profiles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    ghana_card_number = Column(String(30), unique=True)
    date_of_birth = Column(DateTime)
    gender = Column(String(1))  # M/F/O
    address = Column(String(255), nullable=False)
    digital_address = Column(String(20))  # GhanaPostGPS code
    company_name = Column(String(255))
    license_number = Column(String(100))  # For professionals
    specialization = Column(String(100))  # For officers
    
    user = relationship("User", back_populates="profile")

class UserDocument(Base, TimestampMixin):
    __tablename__ = 'user_documents'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    document_type = Column(String(50), nullable=False)
    file_url = Column(String(255), nullable=False)
    
    
    user = relationship(
        "User", 
        back_populates="documents",
        foreign_keys=[user_id] 
    )
    
    def __repr__(self):
        return f"<UserDocument {self.document_type} for User {self.user_id}>"

# Add to core/constants.py


