from sqlalchemy import JSON, Column, String, Integer, Enum, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
from app.core.constants import ReviewStatus, UserRole, VerificationStage
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
    email = Column(String(255), unique=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    other_name = Column(String(100))
    phone = Column(String(20), unique=True)
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


class MMDA(Base, TimestampMixin):
    """Metropolitan/Municipal/District Assembly entity"""
    __tablename__ = 'mmdas'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(20), nullable=False)  # 'metropolitan', 'municipal', 'district'
    region = Column(String(100), nullable=False)
    contact_email = Column(String(255))
    contact_phone = Column(String(20))
    jurisdiction_boundaries = Column(JSON)  # GeoJSON polygon coordinates
    
    # Relationships
    departments = relationship("Department", back_populates="mmda")
    permit_applications = relationship("PermitApplication", back_populates="mmda")
    committees = relationship("Committee", back_populates="mmda")
    
    def __repr__(self):
        return f"<MMDA {self.name} ({self.type})>"

class Department(Base, TimestampMixin):
    """Departments under MMDAs (e.g., Physical Planning)"""
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True)
    mmda_id = Column(Integer, ForeignKey('mmdas.id'), nullable=False)
    name = Column(String(100), nullable=False)  # e.g., "Physical Planning"
    code = Column(String(10), unique=True)  # e.g., "PPD"
    
    # Relationships
    mmda = relationship("MMDA", back_populates="departments")
    staff = relationship("DepartmentStaff", back_populates="department")
    
    def __repr__(self):
        return f"<Department {self.name} ({self.code})>"

class DepartmentStaff(Base, TimestampMixin):
    """Links users to departments with specific roles"""
    __tablename__ = 'department_staff'
    
    id = Column(Integer, primary_key=True)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    position = Column(String(100))  # e.g., "Planning Officer"
    is_head = Column(Boolean, default=False)
    
    # Relationships
    department = relationship("Department", back_populates="staff")
    user = relationship("User")
    
    def __repr__(self):
        return f"<DepartmentStaff {self.user_id} in {self.department_id}>"

class Committee(Base, TimestampMixin):
    """MMDA Committees (e.g., Works Sub-Committee)"""
    __tablename__ = 'committees'
    
    id = Column(Integer, primary_key=True)
    mmda_id = Column(Integer, ForeignKey('mmdas.id'), nullable=False)
    name = Column(String(100), nullable=False)  # e.g., "Works Sub-Committee"
    description = Column(Text)
    
    # Relationships
    mmda = relationship("MMDA", back_populates="committees")
    members = relationship("CommitteeMember", back_populates="committee")
    reviews = relationship("CommitteeReview", back_populates="committee")
    
    def __repr__(self):
        return f"<Committee {self.name}>"

class CommitteeMember(Base, TimestampMixin):
    """Members of MMDA committees"""
    __tablename__ = 'committee_members'
    
    id = Column(Integer, primary_key=True)
    committee_id = Column(Integer, ForeignKey('committees.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(String(50))  # e.g., "Chairperson"
    
    # Relationships
    committee = relationship("Committee", back_populates="members")
    user = relationship("User")
    
    def __repr__(self):
        return f"<CommitteeMember {self.user_id} in {self.committee_id}>"


class CommitteeReview(Base, TimestampMixin):
    __tablename__ = 'committee_reviews'
    
    id = Column(Integer, primary_key=True)
    committee_id = Column(Integer, ForeignKey('committees.id'))
    application_id = Column(Integer, ForeignKey('permit_applications.id'))
    status = Column(Enum(ReviewStatus))
    comments = Column(Text)
    decision_date = Column(DateTime)
    
    # Relationships
    committee = relationship("Committee", back_populates="reviews")
    application = relationship("PermitApplication")