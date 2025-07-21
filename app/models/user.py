from sqlalchemy import JSON, Column, String, Integer, Enum, Boolean, ForeignKey, DateTime, Text, UniqueConstraint
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
    applicant_type_code = Column(String(50), ForeignKey("applicant_types.code"), nullable=True)
    is_active = Column(Boolean, default=False)  # Disabled until Ghana Card verification
    preferred_verification = Column(String(10), default='email')
    role = Column(Enum(UserRole), nullable=False, default=UserRole.APPLICANT)
    verification_stage = Column(Enum(VerificationStage), 
                              default=VerificationStage.OTP_PENDING)  # Tracks verification progress
    date_of_birth = Column(DateTime)
    gender = Column(String(1))  # M/F/O
    address = Column(String(255))
    # Relationships
    applicant_type = relationship("ApplicantType", back_populates="users")
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
    review_steps = relationship("ApplicationReviewStep", back_populates="reviewer")



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

class ApplicantType(Base):
    __tablename__ = "applicant_types"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)  # e.g., "property_owner"
    name = Column(String(100), nullable=False)              # e.g., "Property Owner"
    description = Column(Text, nullable=True)

    users = relationship("User", back_populates="applicant_type", foreign_keys="[User.applicant_type_code]")


class ProfessionalInCharge(Base):
    __tablename__ = "professionals"
    id = Column(Integer, primary_key=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    firm_name = Column(String(255), nullable=True)
    role = Column(String(50), default="architect")  # architect, engineer, etc.
    license_number = Column(String(100))  # optional, depending on context

    applications = relationship("PermitApplication", back_populates="architect")

class UserProfile(Base, TimestampMixin):
    __tablename__ = 'user_profiles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    ghana_card_number = Column(String(30), unique=True)
    digital_address = Column(String(20))  # GhanaPostGPS code
    specialization = Column(String(100))  # For officers
    work_email = Column(String(255), unique=True, nullable=True)
    staff_number = Column(String(50), unique=True, nullable=True, comment="Unique MMDA-issued staff or payroll number")
    designation = Column(String(100))
    
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
    code = Column(String(10))  # e.g., "PPD"
    
    # Relationships
    mmda = relationship("MMDA", back_populates="departments")
    staff = relationship("DepartmentStaff", back_populates="department")
    __table_args__ = (
        UniqueConstraint('mmda_id', 'code', name='uq_department_code_per_mmda'),
    )
    
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