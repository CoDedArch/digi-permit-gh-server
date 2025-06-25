from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List

from app.core.database import aget_db
from app.models.document import PermitTypeModel, PermitDocumentRequirement, DocumentTypeModel
from app.schemas.PermitSchemas import PermitTypeWithRequirements

router = APIRouter(
    prefix="/permits",
    tags=["permits"]
)

@router.get("/types", response_model=List[PermitTypeWithRequirements])
async def get_permit_types_with_requirements(
    db: AsyncSession = Depends(aget_db)
):
    """
    Get all permit types with their document requirements
    
    Returns:
        List of permit types with nested document requirements
    """

    print ("PERMIT REQUEST RECEIVED")
    try:
        # Query permit types with their requirements and document types
        result = await db.execute(
            select(PermitTypeModel)
            .options(
                selectinload(PermitTypeModel.required_documents)
                .selectinload(PermitDocumentRequirement.document_type)
            )
            .order_by(PermitTypeModel.name)
        )
        
        permit_types = result.scalars().all()
        
        if not permit_types:
            raise HTTPException(
                status_code=404,
                detail="No permit types found"
            )
        
        # Sort requirements by mandatory status (mandatory first)
        for permit_type in permit_types:
            permit_type.required_documents.sort(
                key=lambda x: (not x.is_mandatory, x.document_type.name)
            )
        
        return permit_types
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching permit types: {str(e)}"
        )
    
# Get Permit Type by ID 
@router.get("/types/{permit_type_id}", response_model=PermitTypeWithRequirements)
async def get_permit_type_by_id(
    permit_type_id: str,
    db: AsyncSession = Depends(aget_db)
):
    """
    Get a specific permit type by ID with its document requirements
    
    Args:
        permit_type_id: ID of the permit type to retrieve
    
    Returns:
        Permit type with nested document requirements
    
    Raises:
        HTTPException: 404 if permit type not found
        HTTPException: 500 if database error occurs
    """
    print(f"PERMIT TYPE REQUEST RECEIVED FOR ID: {permit_type_id}")
    
    try:
        # Query permit type with its requirements and document types
        result = await db.execute(
            select(PermitTypeModel)
            .where(PermitTypeModel.id == permit_type_id)
            .options(
                selectinload(PermitTypeModel.required_documents)
                .selectinload(PermitDocumentRequirement.document_type)
            )
        )
        
        permit_type = result.scalar_one_or_none()
        
        if not permit_type:
            raise HTTPException(
                status_code=404,
                detail=f"Permit type with ID {permit_type_id} not found"
            )
        
        # Sort requirements by mandatory status (mandatory first)
        permit_type.required_documents.sort(
            key=lambda x: (not x.is_mandatory, x.document_type.name)
        )
        
        return permit_type
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching permit type: {str(e)}"
        )