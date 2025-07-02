from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.core.database import aget_db
from app.models.document import PermitTypeModel, PermitDocumentRequirement, DocumentTypeModel
from app.models.zoning import DrainageType, SiteCondition, ZoningDistrict, ZoningPermittedUse, ZoningUseDocumentRequirement
from app.schemas.PermitSchemas import DrainageTypeOut, PermitTypeOut, PermitTypeWithRequirements, SiteConditionOut, ZoningDistrictOut, ZoningPermittedUseOut

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

@router.get("/permit-types", response_model=List[PermitTypeOut])
async def get_permit_types(db: AsyncSession = Depends(aget_db)):
    result = await db.execute(select(PermitTypeModel).where(PermitTypeModel.is_active == True))
    return result.scalars().all()


@router.get("/zoning-districts", response_model=List[ZoningDistrictOut])
async def get_all_zoning_districts(db: AsyncSession = Depends(aget_db)):
    try:
        result = await db.execute(
            select(ZoningDistrict)
            .order_by(ZoningDistrict.name)
        )
        districts = result.scalars().all()

        # Remove spatial_data explicitly (not included in schema anyway)
        for d in districts:
            d.spatial_data = None  # Optional: strip it if you want

        return districts

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load zoning districts: {str(e)}")

@router.get("/zoning-uses", response_model=List[ZoningPermittedUseOut])
async def get_zoning_uses(
    zoning_district_id: Optional[int] = None,
    db: AsyncSession = Depends(aget_db)
):
    try:
        query = (
            select(ZoningPermittedUse)
            .options(
                selectinload(ZoningPermittedUse.required_documents)
                .selectinload(ZoningUseDocumentRequirement.document_type)
            )
        )

        if zoning_district_id:
            query = query.where(ZoningPermittedUse.zoning_district_id == zoning_district_id)

        result = await db.execute(query)
        uses = result.scalars().all()
        return uses

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load zoning uses: {str(e)}")


@router.get("/drainage-types", response_model=List[DrainageTypeOut])
async def get_all_drainage_types(db: AsyncSession = Depends(aget_db)):
    try:
        result = await db.execute(select(DrainageType).order_by(DrainageType.name))
        return result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch drainage types: {str(e)}")


@router.get("/site-conditions", response_model=List[SiteConditionOut])
async def get_site_conditions(db: AsyncSession = Depends(aget_db)):
    try:
        result = await db.execute(select(SiteCondition).order_by(SiteCondition.name))
        return result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load site conditions: {str(e)}")