import json
from fastapi import APIRouter, Depends, HTTPException, Request
from geoalchemy2 import WKBElement, WKTElement
from requests import session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from sqlalchemy.orm import joinedload
from app.core.database import aget_db
from app.core.security import decode_jwt_token
from app.models.application import PermitApplication
from app.models.document import ApplicationDocument, PermitTypeModel, PermitDocumentRequirement, DocumentTypeModel
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from app.models.user import MMDA, Department, DepartmentStaff
from app.models.zoning import DrainageType, PreviousLandUse, SiteCondition, ZoningDistrict, ZoningPermittedUse, ZoningUseDocumentRequirement
from app.schemas.PermitSchemas import DrainageTypeOut, PermitTypeOut, PermitTypeWithRequirements, PreviousLandUseOut, SiteConditionOut, ZoningDistrictOut, ZoningPermittedUseOut
from app.schemas.permit_application import ApplicationDetailOut, ApplicationOut, ApplicationUpdate

router = APIRouter(
    prefix="/permits",
    tags=["permits"]
)

def serialize_geom(geom):
    if geom is None:
        return None
    if isinstance(geom, dict):
        return geom  # already GeoJSON
    if isinstance(geom, (WKTElement, WKBElement)):
        return mapping(to_shape(geom))  # PostGIS objects
    if isinstance(geom, str):
        try:
            return json.loads(geom)  # maybe stored as GeoJSON string
        except json.JSONDecodeError:
            return geom  # just return as-is
    raise TypeError(f"Unsupported geometry format: {type(geom)}")



@router.get("/my-applications", response_model=List[ApplicationOut])
async def get_user_applications(
    request: Request,
    db: AsyncSession = Depends(aget_db)
):
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_jwt_token(token)
    user_id = int(payload.get("sub"))

    # ✅ Build query
    stmt = (
        select(PermitApplication)
        .where(PermitApplication.applicant_id == user_id)
        .options(
            selectinload(PermitApplication.documents).selectinload(ApplicationDocument.document_type),
            selectinload(PermitApplication.permit_type),
            selectinload(PermitApplication.mmda),
        )
        .order_by(PermitApplication.created_at.desc())
    )

    # ✅ Execute it only once
    result = await db.execute(stmt)
    apps = result.scalars().all()

    print("✅ Final serialized apps:", apps)
    return [ApplicationOut.from_orm(app) for app in apps]

@router.get("/my-applications/{application_id}", response_model=ApplicationDetailOut)
async def get_application(application_id: int, db: AsyncSession = Depends(aget_db)):
    result = await db.execute(
        select(PermitApplication)
        .options(
            joinedload(PermitApplication.zoning_use),
            joinedload(PermitApplication.drainage_type),
            joinedload(PermitApplication.zoning_district),
            joinedload(PermitApplication.previous_land_use),
            joinedload(PermitApplication.site_conditions),
            joinedload(PermitApplication.architect),
            joinedload(PermitApplication.mmda),
            joinedload(PermitApplication.applicant),
            joinedload(PermitApplication.permit_type),
            joinedload(PermitApplication.documents).joinedload(ApplicationDocument.document_type),
            joinedload(PermitApplication.payments),
        )
        .filter(PermitApplication.id == application_id)
    )
    
    app = result.unique().scalar_one_or_none()

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Manually serialize spatial fields to GeoJSON


    data = ApplicationDetailOut.from_orm(app).dict()
    data["parcel_geometry"] = serialize_geom(app.parcel_geometry)
    data["spatial_data"] = serialize_geom(app.spatial_data)
    data["project_location"] = serialize_geom(app.project_location)
    return data


@router.put("/my-applications/{application_id}", response_model=ApplicationUpdate)
async def update_application(
    application_id: int,
    updates: ApplicationUpdate,
    db: AsyncSession = Depends(aget_db)
):
    result = await db.execute(
        select(PermitApplication).where(PermitApplication.id == application_id)
    )
    app = result.scalar_one_or_none()

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    print("App status:", app.status.value)  # or use logger

    if app.status.value not in ("draft", "submitted"):
        raise HTTPException(status_code=400, detail="This application cannot be edited.")

    # Apply updates
    for field, value in updates.dict(exclude_unset=True).items():
        setattr(app, field, value)

    await db.commit()
    await db.refresh(app)

    return app


@router.get("/dashboard/applicant-map")
async def get_dashboard_data(request: Request, db: AsyncSession = Depends(aget_db)):
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = decode_jwt_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Fetch user permits + basic details
    permit_result = await db.execute(
        select(PermitApplication)
        .options(
            joinedload(PermitApplication.mmda),
            joinedload(PermitApplication.permit_type)
        )
        .filter(PermitApplication.applicant_id == user_id)
    )
    permits = permit_result.scalars().all()

    # Group MMDAs related to user’s permits
    mmda_ids = list({permit.mmda_id for permit in permits})

    # Fetch MMDAs + permit stats
    mmda_result = await db.execute(
        select(MMDA)
        .options(selectinload(MMDA.permit_applications))
        .filter(MMDA.id.in_(mmda_ids))
    )
    mmdas = mmda_result.scalars().all()

    mmda_data = []
    for mmda in mmdas:
        permits_in_mmda = mmda.permit_applications
        status_counts = {}
        for permit in permits_in_mmda:
            status = permit.status.value if hasattr(permit.status, "value") else permit.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        mmda_data.append({
            "id": mmda.id,
            "name": mmda.name,
            "region": mmda.region,
            "type": mmda.type,
            "jurisdiction_boundaries": mmda.jurisdiction_boundaries,
            "status_counts": status_counts,
        })
        

    return {
        "permits": [
            {
                "id": p.id,
                "project_name": p.project_name,
                "status": p.status.value if hasattr(p.status, "value") else p.status,
                "permit_type": {"id": p.permit_type.id, "name": p.permit_type.name} if p.permit_type else None,
                "mmda_id": p.mmda_id,
                "parcel_geometry": serialize_geom(p.parcel_geometry),
                "latitude": p.latitude,
                "longitude": p.longitude,
            }
            for p in permits
        ],
        "mmdas": mmda_data,
    }


@router.get("/dashboard/reviewer-map")
async def get_reviewer_dashboard_data(request: Request, db: AsyncSession = Depends(aget_db)):
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = decode_jwt_token(token)
        user_id = int(payload.get("sub"))
        
        # Get the reviewer's department and MMDA info
        staff_result = await db.execute(
            select(DepartmentStaff)
            .join(Department)
            .options(joinedload(DepartmentStaff.department).joinedload(Department.mmda))
            .filter(DepartmentStaff.user_id == user_id)
        )
        staff = staff_result.scalars().first()
        
        if not staff:
            raise HTTPException(status_code=403, detail="User is not a staff member")
        
        mmda_id = staff.department.mmda_id
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Fetch all permits for the reviewer's MMDA (work jurisdiction)
    mmda_permits_result = await db.execute(
        select(PermitApplication)
        .options(
            joinedload(PermitApplication.mmda),
            joinedload(PermitApplication.permit_type)
        )
        .filter(PermitApplication.mmda_id == mmda_id)
    )
    mmda_permits = mmda_permits_result.scalars().all()

    # Fetch any personal permits the reviewer has applied for (in any MMDA)
    personal_permits_result = await db.execute(
        select(PermitApplication)
        .options(
            joinedload(PermitApplication.mmda),
            joinedload(PermitApplication.permit_type)
        )
        .filter(PermitApplication.applicant_id == user_id)
        .filter(PermitApplication.mmda_id != mmda_id)  # Exclude those already in work MMDA
    )
    personal_permits = personal_permits_result.scalars().all()

    print("PERSONAL PERMITS IS", personal_permits)

    # Get IDs of personal permits for efficient checking
    
    personal_permit_ids = {p.id for p in personal_permits}
    
    # Combine both permit lists
    all_permits = mmda_permits + personal_permits

    # Get all unique MMDAs involved (work MMDA + any personal permit MMDAs)
    mmda_ids = {mmda_id} | {p.mmda_id for p in personal_permits}

    # Fetch all relevant MMDAs and their permit stats
    mmdas_data = []
    for current_mmda_id in mmda_ids:
        mmda_result = await db.execute(
            select(MMDA)
            .options(selectinload(MMDA.permit_applications))
            .filter(MMDA.id == current_mmda_id)
        )
        mmda = mmda_result.scalars().first()

        if mmda:
            # Calculate status counts for this MMDA
            status_counts = {
                "submitted": 0,
                "under_review": 0,
                "approved": 0,
                "rejected": 0
            }
            for permit in mmda.permit_applications:
                status = permit.status.value if hasattr(permit.status, "value") else permit.status
                if status in status_counts:
                    status_counts[status] += 1

            mmdas_data.append({
                "id": mmda.id,
                "name": mmda.name,
                "region": mmda.region,
                "type": mmda.type,
                "jurisdiction_boundaries": mmda.jurisdiction_boundaries,
                "status_counts": status_counts,
            })

    return {
        "permits": [
            {
                "id": p.id,
                "project_name": p.project_name,
                "status": p.status.value if hasattr(p.status, "value") else p.status,
                "permit_type": {"id": p.permit_type.id, "name": p.permit_type.name} if p.permit_type else None,
                "mmda_id": p.mmda_id,
                "parcel_geometry": serialize_geom(p.parcel_geometry),
                "latitude": p.latitude,
                "longitude": p.longitude,
                "is_personal": p.id in personal_permit_ids,  # Flag for personal permits
            }
            for p in all_permits
        ],
        "mmdas": mmdas_data,
    }


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
    
@router.get("/previous-land-uses", response_model=List[PreviousLandUseOut])
async def get_previous_land_uses(db: AsyncSession = Depends(aget_db)):
    try:
        result = await db.execute(select(PreviousLandUse).order_by(PreviousLandUse.name))
        return result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load previous land uses: {str(e)}")