import json
from fastapi import APIRouter, Depends, HTTPException, Request
from geoalchemy2 import WKBElement, WKTElement
from requests import session
from sqlalchemy import and_, exists, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from sqlalchemy.orm import joinedload
from app.core.constants import ApplicationStatus, InspectionStatus, UserRole
from app.core.database import aget_db
from app.core.security import decode_jwt_token
from app.models.application import PermitApplication
from app.models.document import ApplicationDocument, PermitTypeModel, PermitDocumentRequirement, DocumentTypeModel
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from app.models.inspection import Inspection
from app.models.user import MMDA, CommitteeMember, Department, DepartmentStaff
from app.models.zoning import DrainageType, PreviousLandUse, SiteCondition, ZoningDistrict, ZoningPermittedUse, ZoningUseDocumentRequirement
from app.schemas.PermitSchemas import DrainageTypeOut, PermitTypeOut, PermitTypeWithRequirements, PreviousLandUseOut, SiteConditionOut, ZoningDistrictOut, ZoningPermittedUseOut
from app.schemas.permit_application import ApplicationDetailOut, ApplicationDocumentOut, ApplicationOut, ApplicationUpdate

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
async def get_reviewer_map_data(
    request: Request, 
    db: AsyncSession = Depends(aget_db)
):
    """Get map data for reviewer dashboard, filtered by department and committee assignments"""
    # Authentication
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = decode_jwt_token(token)
        user_id = int(payload.get("sub"))
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Get reviewer's department and committee assignments
    staff = await get_staff_with_assignments(db, user_id)
    if not staff:
        raise HTTPException(status_code=403, detail="User is not a staff member")

    mmda_id = staff.department.mmda_id

    # Build base filter for applications this reviewer should see
    base_filter = build_reviewer_filter(staff, mmda_id)

    # Fetch relevant permits
    work_permits = await fetch_work_permits(db, base_filter)
    personal_permits = await fetch_personal_permits(db, user_id, mmda_id)
    
    # Process and combine results
    all_permits = work_permits + personal_permits
    personal_permit_ids = {p.id for p in personal_permits}
    mmda_ids = {mmda_id} | {p.mmda_id for p in personal_permits}
    
    # Get MMDA data with statistics
    mmdas_data = await process_mmda_data(db, mmda_ids, staff, mmda_id)

    # Debug logging (keep your existing print statements)
    debug_reviewer_data(base_filter, staff, work_permits, all_permits)

    return format_reviewer_response(all_permits, personal_permit_ids, mmdas_data, mmda_id)

# Helper functions (kept minimal to match your style)
async def get_staff_with_assignments(db: AsyncSession, user_id: int):
    """Get staff member with department and committee assignments"""
    result = await db.execute(
        select(DepartmentStaff)
        .join(Department)
        .options(
            joinedload(DepartmentStaff.department).joinedload(Department.mmda),
            joinedload(DepartmentStaff.committee_memberships).joinedload(CommitteeMember.committee)
        )
        .where(DepartmentStaff.user_id == user_id)
    )
    return result.scalars().first()

def build_reviewer_filter(staff: DepartmentStaff, mmda_id: int):
    """Build filter for applications this reviewer should see"""
    base_filter = and_(
        PermitApplication.mmda_id == mmda_id,
        PermitApplication.department_id == staff.department_id
    )

    if not staff.is_head:
        committee_ids = [cm.committee.id for cm in staff.committee_memberships]
        base_filter = and_(
            base_filter,
            or_(
                PermitApplication.committee_id.in_(committee_ids),
                PermitApplication.committee_id.is_(None)
            )
        )
    return base_filter

async def fetch_work_permits(db: AsyncSession, base_filter):
    """Fetch work permits based on filter"""
    result = await db.execute(
        select(PermitApplication)
        .options(
            joinedload(PermitApplication.mmda),
            joinedload(PermitApplication.permit_type),
            joinedload(PermitApplication.department),
            joinedload(PermitApplication.committee)
        )
        .where(base_filter)
    )
    return result.scalars().all()

async def fetch_personal_permits(db: AsyncSession, user_id: int, mmda_id: int):
    """Fetch personal permits in other MMDAs"""
    result = await db.execute(
        select(PermitApplication)
        .options(
            joinedload(PermitApplication.mmda),
            joinedload(PermitApplication.permit_type)
        )
        .where(
            PermitApplication.applicant_id == user_id,
            PermitApplication.mmda_id != mmda_id
        )
    )
    return result.scalars().all()

async def process_mmda_data(db: AsyncSession, mmda_ids: set, staff: DepartmentStaff, work_mmda_id: int):
    """Process MMDA data with statistics"""
    mmdas_data = []
    for current_mmda_id in mmda_ids:
        mmda = await fetch_mmda(db, current_mmda_id)
        if mmda:
            status_counts = await get_mmda_status_counts(
                db, current_mmda_id, staff, work_mmda_id
            )
            mmdas_data.append(format_mmda_data(mmda, status_counts))
    return mmdas_data

async def fetch_mmda(db: AsyncSession, mmda_id: int):
    """Fetch single MMDA"""
    result = await db.execute(
        select(MMDA)
        .options(selectinload(MMDA.permit_applications))
        .where(MMDA.id == mmda_id)
    )
    return result.scalars().first()

async def get_mmda_status_counts(db: AsyncSession, mmda_id: int, staff: DepartmentStaff, work_mmda_id: int):
    """Get status counts for MMDA permits"""
    status_filter = and_(
        PermitApplication.mmda_id == mmda_id,
        PermitApplication.department_id == staff.department_id if mmda_id == work_mmda_id else True
    )
    
    status_counts_result = await db.execute(
        select(
            PermitApplication.status,
            func.count(PermitApplication.id)
        )
        .where(status_filter)
        .group_by(PermitApplication.status)
    )
    
    status_counts = {
        "submitted": 0,
        "under_review": 0,
        "approved": 0,
        "rejected": 0
    }
    
    for status, count in status_counts_result:
        status_key = status.value if hasattr(status, "value") else status
        if status_key in status_counts:
            status_counts[status_key] = count
    
    return status_counts

def format_mmda_data(mmda: MMDA, status_counts: dict):
    """Format MMDA data for response"""
    return {
        "id": mmda.id,
        "name": mmda.name,
        "region": mmda.region,
        "type": mmda.type,
        "jurisdiction_boundaries": mmda.jurisdiction_boundaries,
        "status_counts": status_counts,
    }

def format_reviewer_response(permits: list, personal_permit_ids: set, mmdas_data: list, reviewer_mmda_id: int):
    """Format final response with reviewer's MMDA ID"""
    return {
        "permits": [
            {
                "id": p.id,
                "project_name": p.project_name,
                "status": p.status.value if hasattr(p.status, "value") else p.status,
                "permit_type": {
                    "id": p.permit_type.id,
                    "name": p.permit_type.name
                } if p.permit_type else None,
                "mmda_id": p.mmda_id,
                "parcel_geometry": serialize_geom(p.parcel_geometry),
                "latitude": p.latitude,
                "longitude": p.longitude,
                "is_personal": p.id in personal_permit_ids,
            }
            for p in permits
        ],
        "mmdas": mmdas_data,
        "reviewer_mmda_id": reviewer_mmda_id,  # Add reviewer's work MMDA ID
    }

def debug_reviewer_data(base_filter, staff, work_permits, all_permits):
    """Debug logging (keeping your existing print statements)"""
    print("Base filter applied", base_filter)
    print("Staff Committee Membership", [
        {"committee_id": cm.committee_id, "role": cm.role} 
        for cm in staff.committee_memberships
    ])
    print("SOMETHING PERMITS:", work_permits)
    print("ALL PERMITS:", all_permits)



@router.get("/dashboard/inspector-map")
async def get_inspector_map_data(
    request: Request, 
    db: AsyncSession = Depends(aget_db)
):
    """Get map data for inspector dashboard including:
    - Inspector's personal applications (any MMDA)
    - Applications ready for inspection in assigned MMDA
    """
    # Authentication
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = decode_jwt_token(token)
        user_id = int(payload.get("sub"))
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Get inspector's department and MMDA info
    staff = await get_inspector_staff_info(db, user_id)
    if not staff:
        raise HTTPException(status_code=403, detail="User is not a staff member")

    mmda_id = staff.department.mmda_id

    try:
        # Fetch applications in two categories:
        # 1. Personal applications (any MMDA)
        personal_applications = await fetch_personal_applications(db, user_id)
        
        # 2. Applications ready for inspection in assigned MMDA
        inspection_ready_apps = await fetch_inspection_ready_apps(db, mmda_id, user_id)

        # Combine and deduplicate
        all_applications = await combine_inspection_data(inspection_ready_apps, personal_applications)
        personal_permit_ids = {p.id for p in personal_applications}
        mmda_ids = {mmda_id} | {app.mmda_id for app in personal_applications}
        
        # Get MMDA data with statistics
        mmdas_data = await process_inspection_mmda_data(db, mmda_ids, mmda_id)

        return format_inspector_response(all_applications, personal_permit_ids, mmdas_data, mmda_id)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

async def get_inspector_staff_info(db: AsyncSession, user_id: int):
    """Get inspector staff member with department info"""
    result = await db.execute(
        select(DepartmentStaff)
        .join(Department)
        .options(
            selectinload(DepartmentStaff.department)
            .selectinload(Department.mmda)
        )
        .where(DepartmentStaff.user_id == user_id)
    )
    return result.scalars().first()

async def fetch_inspection_ready_apps(db: AsyncSession, mmda_id: int, user_id: int):
    """Fetch applications ready for inspection in the specified MMDA"""
    # First get applications that need inspection
    needs_inspection = await db.execute(
        select(PermitApplication)
        .options(
            selectinload(PermitApplication.permit_type),
            selectinload(PermitApplication.mmda),
            selectinload(PermitApplication.inspections)
        )
        .where(
            PermitApplication.mmda_id == mmda_id,
            PermitApplication.status.in_([
                ApplicationStatus.APPROVED,
                ApplicationStatus.UNDER_REVIEW
            ]),
            ~exists().where(Inspection.application_id == PermitApplication.id)
        )
    )
    apps_needing_inspection = needs_inspection.scalars().all()

    # Then get applications with pending inspections assigned to this inspector
    pending_inspections = await db.execute(
        select(PermitApplication)
        .options(
            selectinload(PermitApplication.permit_type),
            selectinload(PermitApplication.mmda),
            selectinload(PermitApplication.inspections)
        )
        .join(Inspection, Inspection.application_id == PermitApplication.id)
        .where(
            PermitApplication.mmda_id == mmda_id,
            Inspection.inspection_officer_id == user_id,
            Inspection.status == InspectionStatus.PENDING
        )
    )
    apps_with_pending = pending_inspections.scalars().all()

    # Combine and deduplicate
    seen_ids = set()
    combined = []
    for app in apps_needing_inspection + apps_with_pending:
        if app.id not in seen_ids:
            seen_ids.add(app.id)
            combined.append(app)
    return combined

async def fetch_personal_applications(db: AsyncSession, user_id: int):
    """Fetch inspector's personal applications from any MMDA"""
    result = await db.execute(
        select(PermitApplication)
        .options(
            selectinload(PermitApplication.permit_type),
            selectinload(PermitApplication.mmda),
            selectinload(PermitApplication.inspections)
        )
        .where(PermitApplication.applicant_id == user_id)
    )
    return result.scalars().all()

async def combine_inspection_data(inspection_ready_apps: list, personal_apps: list):
    """Combine inspection and application data"""
    seen_ids = set()
    unique_apps = []
    
    for app in inspection_ready_apps + personal_apps:
        if app.id not in seen_ids:
            seen_ids.add(app.id)
            unique_apps.append(app)
    
    return unique_apps

async def process_inspection_mmda_data(db: AsyncSession, mmda_ids: set, work_mmda_id: int):
    """Process MMDA data with inspection statistics"""
    mmdas_data = []
    for current_mmda_id in mmda_ids:
        mmda = await fetch_mmda(db, current_mmda_id)
        if mmda:
            status_counts = await get_inspection_status_counts(
                db, current_mmda_id, work_mmda_id
            )
            mmdas_data.append(format_mmda_data(mmda, status_counts))
    return mmdas_data

async def fetch_mmda(db: AsyncSession, mmda_id: int):
    """Fetch single MMDA"""
    result = await db.execute(
        select(MMDA)
        .where(MMDA.id == mmda_id)
    )
    return result.scalars().first()

async def get_inspection_status_counts(db: AsyncSession, mmda_id: int, work_mmda_id: int):
    """Get status counts for inspections in MMDA"""
    # Initialize counts
    status_counts = {
        "pending": 0,
        "scheduled": 0,
        "in_progress": 0,
        "completed": 0,
        "cancelled": 0,
        "awaiting_inspection": 0
    }
    
    # Map inspection statuses
    STATUS_MAPPING = {
        "pending": "pending",
        "scheduled": "scheduled",
        "in_progress": "in_progress",
        "completed": "completed",
        "cancelled": "cancelled",
        "inspected": "completed",
        "approved": "awaiting_inspection",
        "under_review": "awaiting_inspection",
        "inspection_pending": "awaiting_inspection",
        "submitted": "pending",
        "draft": "pending",
        "additional_info_requested": "pending",
        "rejected": "cancelled",
        "issued": "completed",
    }
    
    # Count inspections by status
    inspection_stats = await db.execute(
        select(Inspection.status, func.count(Inspection.id))
        .join(PermitApplication, Inspection.application_id == PermitApplication.id)
        .filter(PermitApplication.mmda_id == mmda_id)
        .group_by(Inspection.status)
    )
    
    for status, count in inspection_stats.all():
        raw = status.value if hasattr(status, "value") else status
        mapped = STATUS_MAPPING.get(raw.lower(), "pending")
        if mapped in status_counts:
            status_counts[mapped] += count
    
    # Count applications needing inspection (only for work MMDA)
    if mmda_id == work_mmda_id:
        needs_inspection_count = await db.execute(
            select(func.count(PermitApplication.id))
            .filter(
                PermitApplication.mmda_id == mmda_id,
                PermitApplication.status.in_([
                    ApplicationStatus.APPROVED,
                    ApplicationStatus.UNDER_REVIEW
                ]),
                ~exists().where(Inspection.application_id == PermitApplication.id)
            )
        )
        status_counts["awaiting_inspection"] += needs_inspection_count.scalar_one() or 0
    
    return status_counts

def format_mmda_data(mmda: MMDA, status_counts: dict):
    """Format MMDA data for response"""
    return {
        "id": mmda.id,
        "name": mmda.name,
        "region": mmda.region,
        "type": mmda.type,
        "jurisdiction_boundaries": mmda.jurisdiction_boundaries,
        "status_counts": status_counts,
    }

def format_inspector_response(applications: list, personal_permit_ids: set, mmdas_data: list, inspector_mmda_id: int):
    """Format final response for inspector map"""
    print("MMDA Data:", mmdas_data)  # Debugging output
    return {
        "permits": [
            {
                "id": app.id,
                "project_name": app.project_name,
                "status": app.status.value if hasattr(app.status, "value") else app.status,
                "permit_type": {
                    "id": app.permit_type.id,
                    "name": app.permit_type.name
                } if app.permit_type else None,
                "mmda_id": app.mmda_id,
                "parcel_geometry": serialize_geom(app.parcel_geometry),
                "latitude": app.latitude,
                "longitude": app.longitude,
                "is_personal": app.id in personal_permit_ids,
                "inspections": [
                    {
                        "id": insp.id,
                        "status": insp.status.value if hasattr(insp.status, "value") else insp.status,
                        "scheduled_date": insp.scheduled_date.isoformat() if insp.scheduled_date else None,
                        "actual_date": insp.actual_date.isoformat() if insp.actual_date else None,
                        "inspection_type": insp.inspection_type.value if insp.inspection_type else None,
                        "outcome": insp.outcome.value if insp.outcome else None,
                        "officer_id": insp.inspection_officer_id
                    }
                    for insp in app.inspections
                ],
                "needs_inspection": (
                    app.status in [ApplicationStatus.APPROVED, ApplicationStatus.UNDER_REVIEW]
                    and len(app.inspections) == 0
                )
            }
            for app in applications
        ],
        "mmdas": mmdas_data,
        "inspector_mmda_id": inspector_mmda_id,  # Add inspector's work MMDA ID
    }

@router.get("/dashboard/admin-map")
async def get_admin_dashboard_map(request: Request, db: AsyncSession = Depends(aget_db)):
    """Get comprehensive dashboard data for admin users including permits, MMDAs, and departments"""
    # Authentication
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = decode_jwt_token(token)
        user_id = int(payload.get("sub"))
        
        # Get the admin's department and MMDA info
        staff_result = await db.execute(
            select(DepartmentStaff)
            .join(Department)
            .options(
                joinedload(DepartmentStaff.department)
                .joinedload(Department.mmda)
            )
            .filter(DepartmentStaff.user_id == user_id)
        )
        staff = staff_result.scalars().first()
        
        if not staff:
            raise HTTPException(status_code=403, detail="User is not a staff member")
        
        mmda_id = staff.department.mmda_id
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Fetch all permits for the admin's MMDA (administrative jurisdiction)
    mmda_permits_result = await db.execute(
        select(PermitApplication)
        .options(
            joinedload(PermitApplication.mmda),
            joinedload(PermitApplication.permit_type),
            joinedload(PermitApplication.applicant),
            joinedload(PermitApplication.department)
        )
        .filter(PermitApplication.mmda_id == mmda_id)
    )
    mmda_permits = mmda_permits_result.scalars().all()

    # Fetch any personal permits the admin has applied for (in any MMDA)
    personal_permits_result = await db.execute(
        select(PermitApplication)
        .options(
            joinedload(PermitApplication.mmda),
            joinedload(PermitApplication.permit_type),
            joinedload(PermitApplication.applicant)
        )
        .filter(PermitApplication.applicant_id == user_id)
        .filter(PermitApplication.mmda_id != mmda_id)  # Exclude those already in work MMDA
    )
    personal_permits = personal_permits_result.scalars().all()

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

    # Fetch departments within the admin's MMDA with accurate application counts
    departments_result = await db.execute(
        select(Department)
        .filter(Department.mmda_id == mmda_id)
    )
    departments = departments_result.scalars().all()

    departments_data = []
    for dept in departments:
        # Count staff in this department
        staff_count_result = await db.execute(
            select(func.count(DepartmentStaff.user_id))
            .filter(DepartmentStaff.department_id == dept.id)
        )
        staff_count = staff_count_result.scalar_one() or 0

        # Count active applications for this department
        active_apps_result = await db.execute(
            select(func.count(PermitApplication.id))
            .filter(PermitApplication.department_id == dept.id)
            .filter(
                PermitApplication.status.in_([
                    ApplicationStatus.SUBMITTED,
                    ApplicationStatus.UNDER_REVIEW
                ])
            )
        )
        active_apps = active_apps_result.scalar_one() or 0

        # Count total applications for this department
        total_apps_result = await db.execute(
            select(func.count(PermitApplication.id))
            .filter(PermitApplication.department_id == dept.id)
        )
        total_apps = total_apps_result.scalar_one() or 0

        # Get status breakdown for this department
        status_counts_result = await db.execute(
            select(
                PermitApplication.status,
                func.count(PermitApplication.id)
            )
            .filter(PermitApplication.department_id == dept.id)
            .group_by(PermitApplication.status)
        )
        status_counts = {
            status.value if hasattr(status, "value") else status: count 
            for status, count in status_counts_result
        }

        departments_data.append({
            "id": dept.id,
            "name": dept.name,
            "code": dept.code,
            "mmda_id": dept.mmda_id,
            "staff_count": staff_count,
            "active_applications": active_apps,
            "total_applications": total_apps,
            "status_counts": status_counts,
        })

    return {
        "permits": [
            {
                "id": p.id,
                "application_number": p.application_number,
                "project_name": p.project_name,
                "status": p.status.value if hasattr(p.status, "value") else p.status,
                "permit_type": {
                    "id": p.permit_type.id,
                    "name": p.permit_type.name
                } if p.permit_type else None,
                "mmda_id": p.mmda_id,
                "parcel_geometry": serialize_geom(p.parcel_geometry),
                "latitude": p.latitude,
                "longitude": p.longitude,
                "is_personal": p.id in personal_permit_ids,
                "applicant_name": f"{p.applicant.first_name} {p.applicant.last_name}" if p.applicant else "Unknown",
                "department_id": p.department_id,
            }
            for p in all_permits
        ],
        "mmdas": mmdas_data,
        "departments": departments_data,
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