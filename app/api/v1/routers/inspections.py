import traceback
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime, timezone

from app.core.constants import ApplicationStatus, InspectionOutcome, UserRole
from app.core.database import aget_db
from app.models.document import ApplicationDocument
from app.models.inspection import Inspection, InspectionPhoto, InspectionStatus, InspectionType
from app.models.application import ApplicationStatusHistory, PermitApplication
from app.models.user import MMDA, User
from app.schemas.InspectionSchema import InspectionCompleteIn, InspectionDetailOut, InspectionOut, InspectionPhotoOut, InspectionRequest, InspectorViolationOut, PaginatedViolationsOut
from app.core.security import decode_jwt_token
from app.schemas.permit_application import ApplicationDocumentOut  # make sure this function exists

router = APIRouter(
    prefix="/inspections",
    tags=["inspections"]
)

@router.post("/request", status_code=status.HTTP_201_CREATED)
async def request_inspection(
    request: Request,
    payload: InspectionRequest,
    db: AsyncSession = Depends(aget_db),
):
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        decoded = decode_jwt_token(token)
        user_id = int(decoded.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    app_result = await db.execute(
        select(PermitApplication)
        .options(joinedload(PermitApplication.mmda))
        .where(PermitApplication.id == payload.application_id)
    )
    application = app_result.scalar_one_or_none()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if application.applicant_id != user_id:
        raise HTTPException(status_code=403, detail="You do not own this application")

    inspection = Inspection(
    application_id=application.id,
    applicant_id=user_id,
    mmda_id=application.mmda_id,
    inspection_type=payload.inspection_type,
    scheduled_date=datetime.combine(payload.requested_date, datetime.min.time()),
    status=InspectionStatus.PENDING,
    notes=payload.notes,
    is_reinspection=False
)


    db.add(inspection)
    await db.commit()
    await db.refresh(inspection)

    return {"message": "Inspection request submitted", "inspection_id": inspection.id}



@router.get("/user")
async def get_user_inspections(
    request: Request,
    db: AsyncSession = Depends(aget_db),
):
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        decoded = decode_jwt_token(token)
        user_id = int(decoded.get("sub"))
        user_role = decoded.get("role")  # make sure you include this in your token
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Inspections requested by this user
    requested_stmt = (
        select(Inspection)
        .options(
            joinedload(Inspection.application),
            joinedload(Inspection.inspection_officer),
        )
        .where(Inspection.applicant_id == user_id)
    )

    requested_result = await db.execute(requested_stmt)
    requested_inspections = requested_result.scalars().unique().all()

    assigned_inspections = []
    if user_role == "inspection_officer":
        assigned_stmt = (
            select(Inspection)
            .options(
                joinedload(Inspection.application),
                joinedload(Inspection.inspection_officer),
            )
            .where(Inspection.inspection_officer_id == user_id)
        )

        assigned_result = await db.execute(assigned_stmt)
        assigned_inspections = assigned_result.scalars().unique().all()

    return {
        "requested": [InspectionOut.from_orm(i) for i in requested_inspections],
        "assigned": [InspectionOut.from_orm(i) for i in assigned_inspections],
    }

    

@router.get("/{inspection_id}", response_model=InspectionDetailOut)
async def get_inspection_detail(
    inspection_id: int,
    request: Request,
    db: AsyncSession = Depends(aget_db),
):
    # Verify authentication
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Decode token to verify user
        payload = decode_jwt_token(token)
        user_id = payload.get("sub")
        user_role = payload.get("role")

        # Get inspection with all relationships loaded
        stmt = (
            select(Inspection)
            .options(
                selectinload(Inspection.application).load_only(
                    PermitApplication.id,
                    PermitApplication.application_number,
                    PermitApplication.project_name,
                    PermitApplication.project_description,
                    PermitApplication.project_address,
                ),
                selectinload(Inspection.application).selectinload(PermitApplication.permit_type),
                selectinload(Inspection.inspection_officer).load_only(
                    User.id,
                    User.first_name,
                    User.last_name,
                    User.phone,
                ),
                selectinload(Inspection.applicant).load_only(
                    User.id,
                    User.first_name,
                    User.last_name,
                    User.email,
                    User.phone,
                ),
                selectinload(Inspection.mmda).load_only(
                    MMDA.id,
                    MMDA.name,
                ),
                selectinload(Inspection.photos).selectinload(InspectionPhoto.uploaded_by),
            )
            .where(Inspection.id == inspection_id)
        )

        result = await db.execute(stmt)
        inspection = result.scalar_one_or_none()

        if not inspection:
            raise HTTPException(status_code=404, detail="Inspection not found")

        # Convert to dict first to avoid async issues
        inspection_dict = {
            "id": inspection.id,
            "inspection_type": inspection.inspection_type,
            "status": inspection.status,
            "outcome": inspection.outcome,
            "scheduled_date": inspection.scheduled_date,
            "actual_date": inspection.actual_date,
            "notes": inspection.notes,
            "is_reinspection": inspection.is_reinspection,
            "special_instructions": inspection.special_instructions if hasattr(inspection, 'special_instructions') else None,
            "findings": inspection.findings,
            "recommendations": inspection.recommendations,
            "violations_found": inspection.violations_found,
            "application": inspection.application,
            "inspection_officer": inspection.inspection_officer,
            "applicant": inspection.applicant,
            "mmda": inspection.mmda,
            "photos": [
                {
                    "id": photo.id,
                    "file_url": photo.file_path,  # Note: Changed from file_url to file_path
                    "caption": photo.caption,
                    "uploaded_at": photo.uploaded_at,
                    "uploaded_by": photo.uploaded_by,
                    "inspection_id": photo.inspection_id
                }
                for photo in inspection.photos
                ] if inspection.photos else []
        }

        return InspectionDetailOut(**inspection_dict)

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching inspection details: {str(e)}"
        )

@router.get("/{inspection_id}/documents", response_model=List[ApplicationDocumentOut])
async def get_inspection_documents(
    inspection_id: int,
    request: Request,
    db: AsyncSession = Depends(aget_db)
):
    # Verify authentication
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_jwt_token(token)
    user_id = int(payload.get("sub"))

    # 🔍 Get actual user role from DB
    user_result = await db.execute(
        select(User.role).where(User.id == user_id)
    )
    user_role = user_result.scalar_one_or_none()

    if user_role != UserRole.INSPECTION_OFFICER:
        raise HTTPException(
            status_code=403,
            detail="Only inspectors can access inspection documents"
        )

    # Get the inspection
    inspection_result = await db.execute(
        select(Inspection)
        .where(Inspection.id == inspection_id)
        .options(joinedload(Inspection.application))
    )
    inspection = inspection_result.scalar_one_or_none()

    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    # Get documents for the application
    docs_result = await db.execute(
        select(ApplicationDocument)
        .where(ApplicationDocument.application_id == inspection.application_id)
        .options(selectinload(ApplicationDocument.document_type))
        .order_by(ApplicationDocument.uploaded_at.desc())
    )
    documents = docs_result.scalars().all()

    return [ApplicationDocumentOut.from_orm(doc) for doc in documents]

@router.get("/{inspection_id}/photos", response_model=List[InspectionPhotoOut])
async def get_inspection_photos(
    inspection_id: int,
    request: Request,
    db: AsyncSession = Depends(aget_db)
):
    # Verify authentication
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_jwt_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Verify user is inspection officer
    user = await db.get(User, user_id)
    if not user or user.role != UserRole.INSPECTION_OFFICER:
        raise HTTPException(
            status_code=403,
            detail="Only inspection officers can access inspection photos"
        )

    # Verify inspection exists
    inspection = await db.get(Inspection, inspection_id)
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    # Get photos for the inspection
    photos_result = await db.execute(
        select(InspectionPhoto)
        .where(InspectionPhoto.inspection_id == inspection_id)
        .options(selectinload(InspectionPhoto.uploaded_by))
        .order_by(InspectionPhoto.uploaded_at.desc())
    )
    photos = photos_result.scalars().all()

    return [InspectionPhotoOut.from_orm(photo) for photo in photos]

from fastapi import status

@router.post("/{inspection_id}/complete", status_code=status.HTTP_200_OK)
async def complete_inspection(
    inspection_id: int,
    request: Request,
    inspection_data: InspectionCompleteIn,
    db: AsyncSession = Depends(aget_db)
):
    # Authentication
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_jwt_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Authorization - must be inspection officer
    user = await db.get(User, user_id)
    if not user or user.role != UserRole.INSPECTION_OFFICER:
        raise HTTPException(
            status_code=403,
            detail="Only inspection officers can complete inspections"
        )

    # Get inspection with application relationship loaded
    inspection = await db.execute(
        select(Inspection)
        .options(selectinload(Inspection.application))
        .where(Inspection.id == inspection_id)
    )
    inspection = inspection.scalar_one_or_none()

    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    # Verify inspection isn't already completed
    if inspection.status == InspectionStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Inspection is already completed"
        )

    # Update inspection
    inspection.status = InspectionStatus.COMPLETED
    inspection.outcome = inspection_data.outcome
    inspection.notes = inspection_data.notes
    inspection.violations_found = inspection_data.violations_found
    inspection.actual_date = datetime.utcnow()
    
    # Set recommendation based on outcome
    if inspection_data.outcome == InspectionOutcome.PASSED:
        inspection.recommendations = "APPROVE - All requirements met"
    elif inspection_data.outcome == InspectionOutcome.FAILED:
        inspection.recommendations = "REJECT - Significant violations found"
    elif inspection_data.outcome == InspectionOutcome.PARTIAL:
        inspection.recommendations = "CONDITIONAL APPROVAL - Minor issues to rectify"
    else:
        inspection.recommendations = "PENDING REVIEW - Unknown outcome"

    # Update application status to INSPECTION_COMPLETED
    if inspection.application:
        inspection.application.status = ApplicationStatus.INSPECTION_COMPLETED
        # Add status history record
        status_history = ApplicationStatusHistory(
            application_id=inspection.application.id,
            from_status=inspection.application.status,
            to_status=ApplicationStatus.INSPECTION_COMPLETED,
            changed_by_id=user_id,
            notes=f"Inspection completed by {user.first_name} {user.last_name}"
        )
        db.add(status_history)

    # Handle photos (create records for any new photos)
    if inspection_data.photos:
        for photo_data in inspection_data.photos:
            photo = InspectionPhoto(
                inspection_id=inspection_id,
                file_path=photo_data.file_path,
                caption=photo_data.caption,
                uploaded_by_id=user_id
            )
            db.add(photo)

    try:
        await db.commit()
        return {"message": "Inspection completed successfully"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error completing inspection: {str(e)}"
        )


@router.get("/application/{application_id}", response_model=InspectionDetailOut)
async def get_inspection_by_application(
    application_id: int,
    request: Request,
    db: AsyncSession = Depends(aget_db),
):
    # Verify authentication
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Decode token to verify user
        payload = decode_jwt_token(token)
        user_id = payload.get("sub")
        user_role = payload.get("role")

        # Get inspection for this application with all relationships loaded
        stmt = (
            select(Inspection)
            .options(
                selectinload(Inspection.application).load_only(
                    PermitApplication.id,
                    PermitApplication.application_number,
                    PermitApplication.project_name,
                    PermitApplication.project_description,
                    PermitApplication.project_address,
                ),
                selectinload(Inspection.application).selectinload(PermitApplication.permit_type),
                selectinload(Inspection.inspection_officer).load_only(
                    User.id,
                    User.first_name,
                    User.last_name,
                    User.phone,
                ),
                selectinload(Inspection.applicant).load_only(
                    User.id,
                    User.first_name,
                    User.last_name,
                    User.email,
                    User.phone,
                ),
                selectinload(Inspection.mmda).load_only(
                    MMDA.id,
                    MMDA.name,
                ),
                selectinload(Inspection.photos).selectinload(InspectionPhoto.uploaded_by),
            )
            .where(Inspection.application_id == application_id)
            .order_by(Inspection.scheduled_date.desc())
        )

        result = await db.execute(stmt)
        inspection = result.scalar_one_or_none()

        if not inspection:
            raise HTTPException(status_code=404, detail="No inspection found for this application")

        # Convert to dict first to avoid async issues
        inspection_dict = {
            "id": inspection.id,
            "inspection_type": inspection.inspection_type,
            "status": inspection.status,
            "outcome": inspection.outcome,
            "scheduled_date": inspection.scheduled_date,
            "actual_date": inspection.actual_date,
            "notes": inspection.notes,
            "is_reinspection": inspection.is_reinspection,
            "special_instructions": inspection.special_instructions if hasattr(inspection, 'special_instructions') else None,
            "findings": inspection.findings,
            "recommendations": inspection.recommendations,
            "violations_found": inspection.violations_found,
            "application": inspection.application,
            "inspection_officer": inspection.inspection_officer,
            "applicant": inspection.applicant,
            "mmda": inspection.mmda,
            "photos": [
                {
                    "id": photo.id,
                    "file_url": photo.file_path,
                    "caption": photo.caption,
                    "uploaded_at": photo.uploaded_at,
                    "uploaded_by": photo.uploaded_by,
                    "inspection_id": photo.inspection_id
                }
                for photo in inspection.photos
            ] if inspection.photos else []
        }

        return InspectionDetailOut(**inspection_dict)

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching inspection details: {str(e)}"
        )
    

import traceback
from fastapi import HTTPException

@router.post("/reviewer-schedule", status_code=201)
async def reviewer_schedule_inspection(
    request: Request,
    db: AsyncSession = Depends(aget_db),
):
    try:
        # Authentication
        token = request.cookies.get("auth_token")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        try:
            payload = decode_jwt_token(token)
            user_id = int(payload.get("sub"))
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        # Authorization - must be reviewer
        user = await db.get(User, user_id)
        print("user", user.role != UserRole.REVIEW_OFFICER)
        if not user or user.role != UserRole.REVIEW_OFFICER:
            raise HTTPException(
                status_code=403,
                detail="Only reviewers can schedule inspections"
            )
        
        # --- Step 2: Parse and validate input ---
        body = await request.json()
        
        application_id = body.get("application_id")
        print("Application: ", application_id)
        if not application_id:
            raise HTTPException(status_code=400, detail="application_id is required")

        inspection_date = body.get("scheduled_date")

        print("Application: ", application_id)
        if not inspection_date:
            raise HTTPException(status_code=400, detail="inspection_date is required")

        print("Application: ", application_id)
        try:
            dt = datetime.fromisoformat(inspection_date.replace("Z", "+00:00"))
            inspection_dt = dt.astimezone(timezone.utc).replace(tzinfo=None)

            if inspection_dt < datetime.utcnow():
                raise HTTPException(status_code=400, detail="Inspection date must be in the future")
            print("Application: ", application_id)
            
        except ValueError as e:
            traceback.print_exc()
            raise HTTPException(status_code=400, detail="Invalid inspection_date format")

        inspection_type = body.get("inspection_type", "initial")
        if inspection_type not in [t.value for t in InspectionType]:
            raise HTTPException(status_code=400, detail=f"Invalid inspection_type. Must be one of: {[t.value for t in InspectionType]}")

        # --- Step 3: Fetch and validate application ---
        result = await db.execute(
            select(PermitApplication)
            .where(PermitApplication.id == application_id)
            .options(selectinload(PermitApplication.applicant))
        )
        application = result.scalar_one_or_none()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        # --- Step 4: Create inspection record ---
        inspection = Inspection(
            application_id=application_id,
            inspection_officer_id=None,
            applicant_id=application.applicant_id,
            mmda_id=application.mmda_id,
            inspection_type=InspectionType(inspection_type),
            status=InspectionStatus.SCHEDULED,
            scheduled_date=inspection_dt,
            actual_date=inspection_dt,
            notes=body.get("notes", ""),
            special_instructions=body.get("special_instructions", ""),
            is_reinspection=body.get("is_reinspection", False),
        )
        db.add(inspection)

        # --- Step 5: Update application status ---
        application.status = ApplicationStatus.INSPECTION_PENDING
        application.updated_at = datetime.utcnow()

        # --- Step 6: Record status history ---
        status_history = ApplicationStatusHistory(
            application_id=application_id,
            from_status=application.status,
            to_status=ApplicationStatus.INSPECTION_PENDING,
            changed_by_id=user_id,
            notes=f"Inspection scheduled for {inspection_dt.isoformat()}",
        )
        db.add(status_history)

        await db.commit()

        return {
            "success": True,
            "inspection_id": inspection.id,
            "scheduled_date": inspection_dt.isoformat(),
            "application_status": "inspection_pending"
        }

    except HTTPException:
        # Re-raise HTTP exceptions as they are
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while scheduling inspection: {str(e)}"
        )