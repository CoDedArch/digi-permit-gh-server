from sqlalchemy import Enum as SQLEnum, Numeric
import logging
from sqlalchemy import JSON, Column, String, Enum, Integer, ForeignKey, Boolean, DateTime, UniqueConstraint, func, select
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base, TimestampMixin
from app.core.constants import DocumentStatus, PermitType, ZoneType

logger = logging.getLogger(__name__)

# Database model
class DocumentTypeModel(Base):
    __tablename__ = "document_types"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    code = Column(String, unique=True)
    description = Column(String)
    is_custom = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    permit_requirements = relationship(
        "PermitDocumentRequirement",
        back_populates="document_type",
        cascade="all, delete-orphan"
    )
    
    application_documents = relationship(
        "ApplicationDocument",
        back_populates="document_type",
        cascade="all, delete-orphan"
    )

class PermitTypeModel(Base):
    __tablename__ = "permit_types"
    
    id = Column(String(50), primary_key=True)  # Simple action-based types
    name = Column(String(100), nullable=False)
    description = Column(String)
    is_active = Column(Boolean, default=True)
    base_fee = Column(Numeric(10, 2), nullable=False)  # e.g., 100.00
    standard_duration_days = Column(Integer, nullable=False)  # e.g., 30 (days)
    
    # Relationships
    required_documents = relationship(
        "PermitDocumentRequirement",
        back_populates="permit_type",
        cascade="all, delete-orphan"
    )
    applications = relationship("PermitApplication", back_populates="permit_type")

# Updated junction table with zoning awareness
class PermitDocumentRequirement(Base):
    __tablename__ = "permit_document_requirements"
    
    id = Column(Integer, primary_key=True)
    permit_type_id = Column(String(50), ForeignKey('permit_types.id'))
    document_type_id = Column(Integer, ForeignKey('document_types.id'))
    # Attributes
    is_mandatory = Column(Boolean, default=True)
    conditional_logic = Column(JSON, nullable=True)
    notes = Column(String, nullable=True)
    phase = Column(String(50))  # "application", "approval", "construction"
    
    # Relationships
    permit_type = relationship("PermitTypeModel", back_populates="required_documents")
    document_type = relationship("DocumentTypeModel", back_populates="permit_requirements")
    


class ApplicationDocument(Base):
    __tablename__ = 'application_documents'
    
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('permit_applications.id'))
    document_type_id = Column(Integer, ForeignKey('document_types.id'))
    file_path = Column(String(512), nullable=False)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING)
    uploaded_by_id = Column(Integer, ForeignKey('users.id'))
    uploaded_at = Column(DateTime, server_default=func.now())
    reviewed_at = Column(DateTime)
    
    application = relationship("PermitApplication", back_populates="documents")
    document_type = relationship("DocumentTypeModel", back_populates="application_documents")
    uploaded_by = relationship("User")