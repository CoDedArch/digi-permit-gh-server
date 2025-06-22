from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.constants import DOCUMENT_MAP
from app.models.document import PermitTypeModel, PermitDocumentRequirement, DocumentTypeModel

class PermitSystemInitializer:
    
    @classmethod
    async def initialize_document_types(cls, db: AsyncSession):
        """Create all document types from the comprehensive map"""
        all_documents = set()
        for requirements in DOCUMENT_MAP.values():
            all_documents.update(requirements)
            
        for doc_name in all_documents:
            # Create a code by simplifying the name
            doc_code = doc_name.upper().replace(" ", "_").replace("(", "").replace(")", "")
            existing = await db.execute(
                select(DocumentTypeModel).where(DocumentTypeModel.name == doc_name)
            )
            if not existing.scalar():
                db.add(DocumentTypeModel(
                    code=doc_code,
                    name=doc_name,
                    description=f"Required for {doc_name.replace('(', '').replace(')', '')}"
                ))
        await db.commit()
    
    @classmethod
    async def initialize_permit_requirements(cls, db: AsyncSession):
        """Set up all permit-document relationships from DOCUMENT_MAP"""
        for permit_type, doc_names in DOCUMENT_MAP.items():
            # Get the permit type from DB
            permit = await db.execute(
                select(PermitTypeModel).where(PermitTypeModel.id == permit_type.value))
            
            permit = permit.scalar()
            
            if not permit:
                continue
                
            # Get all related documents
            documents = await db.execute(
                select(DocumentTypeModel).where(DocumentTypeModel.name.in_(doc_names)))
            documents = documents.scalars().all()
            
            # Create requirements
            for doc in documents:
                existing = await db.execute(
                    select(PermitDocumentRequirement).where(
                        PermitDocumentRequirement.permit_type_id == permit.id,
                        PermitDocumentRequirement.document_type_id == doc.id
                    ))
                if not existing.scalar():
                    is_mandatory = not ("if applicable" in doc.name.lower())
                    db.add(PermitDocumentRequirement(
                        permit_type_id=permit.id,
                        document_type_id=doc.id,
                        is_mandatory=is_mandatory,
                        phase="application"  # Default phase
                    ))
        await db.commit()