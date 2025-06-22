import logging
from sqlalchemy import JSON, Column, String, Enum, Integer, ForeignKey, Boolean, DateTime, UniqueConstraint, select
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base, TimestampMixin
from app.core.constants import DocumentType, DocumentStatus, PermitType

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


class PermitTypeModel(Base):
    __tablename__ = "permit_types"
    
    id = Column(String(50), primary_key=True)  # Using the enum value as primary key
    name = Column(String(100), nullable=False)
    description = Column(String)
    requires_epa_approval = Column(Boolean, default=False)
    requires_heritage_review = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Relationship with document types
    required_documents = relationship(
        "PermitDocumentRequirement",
        back_populates="permit_type",
        cascade="all, delete-orphan"
    )
    
    @classmethod
    async def seed_defaults(cls, db: AsyncSession):
        """Enhanced seeding with transaction safety"""
        try:
            for permit in PermitType:
                # Use merge to handle conflicts gracefully
                stmt = select(cls).where(cls.id == permit.value)
                result = await db.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if not existing:
                    permit_data = {
                        "id": permit.value,
                        "name": permit.name.replace("_", " ").title(),
                        "description": f"Default {permit.value} permit type",
                        "requires_epa_approval": "epa" in permit.name.lower(),
                        "requires_heritage_review": "heritage" in permit.name.lower()
                    }
                    db.add(cls(**permit_data))
                    logger.debug(f"Added permit type: {permit.value}")
            
            await db.flush()
        except Exception as e:
            logger.error(f"Error seeding permit types: {e}")
            await db.rollback()
            raise


# Junction Table for many-to-many relationship
class PermitDocumentRequirement(Base):
    __tablename__ = "permit_document_requirements"
    
    id = Column(Integer, primary_key=True)
    permit_type_id = Column(String(50), ForeignKey('permit_types.id'))
    document_type_id = Column(Integer, ForeignKey('document_types.id'))
    is_mandatory = Column(Boolean, default=True)
    conditional_logic = Column(JSON, nullable=True)  # For complex requirementss
    notes = Column(String, nullable=True)
    phase = Column(String(50))  # "application", "approval", "construction"
    
    # Relationships
    permit_type = relationship("PermitTypeModel", back_populates="required_documents")
    document_type = relationship("DocumentTypeModel", back_populates="permit_requirements")
    
    __table_args__ = (
        UniqueConstraint('permit_type_id', 'document_type_id', name='uq_permit_document'),
    )



class ApplicationDocument(Base, TimestampMixin):
    __tablename__ = 'application_documents'
    
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('permit_applications.id'), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)  # in bytes
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING)
    rejection_reason = Column(String(255))
    
    # Relationships
    application = relationship("PermitApplication", back_populates="documents")
    
    def __repr__(self):
        return f"<ApplicationDocument {self.file_name} ({self.document_type.value})>"