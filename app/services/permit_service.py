from app.models.document import DocumentTypeModel, PermitDocumentRequirement
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict
from sqlalchemy import select



class PermitService:
    
    @staticmethod
    async def get_requirements_for_permit(
        db: AsyncSession,
        permit_type_id: str,
        phase: str = None
    ) -> List[Dict]:
        """Get all document requirements for a permit type"""
        query = select(
            DocumentTypeModel,
            PermitDocumentRequirement.is_mandatory,
            PermitDocumentRequirement.notes
        ).join(
            PermitDocumentRequirement,
            PermitDocumentRequirement.document_type_id == DocumentTypeModel.id
        ).where(
            PermitDocumentRequirement.permit_type_id == permit_type_id
        )
        
        if phase:
            query = query.where(PermitDocumentRequirement.phase == phase)
            
        result = await db.execute(query)
        return [
            {
                "document_id": doc.id,
                "document_code": doc.code,
                "document_name": doc.name,
                "is_mandatory": is_mandatory,
                "notes": notes
            }
            for doc, is_mandatory, notes in result.all()
        ]
    
    @staticmethod
    async def validate_application(
        db: AsyncSession,
        permit_type_id: str,
        submitted_docs: List[int]
    ) -> Dict:
        """Validate if submitted documents meet requirements"""
        requirements = await PermitService.get_requirements_for_permit(db, permit_type_id)
        
        missing_mandatory = [
            req for req in requirements 
            if req["is_mandatory"] and req["document_id"] not in submitted_docs
        ]
        
        return {
            "is_valid": len(missing_mandatory) == 0,
            "missing_documents": missing_mandatory,
            "optional_documents": [
                req for req in requirements
                if not req["is_mandatory"] and req["document_id"] not in submitted_docs
            ]
        }