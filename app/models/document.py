from sqlalchemy import Column, String, Enum, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
from app.core.constants import DocumentType, DocumentStatus

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