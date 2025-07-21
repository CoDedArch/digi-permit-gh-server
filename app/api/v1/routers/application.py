# app/api/v1/routers/applications.py
from datetime import datetime, timezone
import json
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from uuid import uuid4
from app.api.v1.routers.documents import serialize_geom
from app.core.constants import InspectionStatus, InspectionType, PaymentPurpose, PaymentStatus, ReviewOutcome, ReviewStatus
from app.core.database import aget_db
from sqlalchemy.orm import joinedload
from app.core.security import decode_jwt_token
from app.models.application import ApplicationStatusHistory, PermitApplication, ApplicationStatus
from app.models.document import ApplicationDocument
from app.models.inspection import Inspection
from app.models.payment import Payment
from app.models.review import ApplicationReview, ApplicationReviewStep
from app.models.zoning import SiteCondition
from app.schemas.ReviewPermitSchemas import FlagStepRequest, ReviewerPermitApplicationOut, UpdateReviewStatusRequest
from app.schemas.permit_application import PermitApplicationCreate
from app.models.user import MMDA, Committee, CommitteeMember, ProfessionalInCharge, User
from app.services.geojson_to_ewkt import geojson_to_ewkt

router = APIRouter(prefix="/applications", tags=["applications"])

@router.post("/submit-application")
async def create_application(
    data: PermitApplicationCreate,
    request: Request,
    db: AsyncSession = Depends(aget_db)
):
    print("request Received")
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_jwt_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    architect_id = None

    print("Site conditions are: ", data.siteConditionIds)
    
    if data.architect and (data.architect.full_name or data.architect.license_number):
        new_professional = ProfessionalInCharge(
            full_name=data.architect.full_name,
            email=data.architect.email,
            phone=data.architect.phone,
            firm_name=data.architect.firm_name,
            license_number=data.architect.license_number,
            role=data.architect.role or "architect",
        )
        db.add(new_professional)
        await db.flush()  # Get the ID before commit
        architect_id = new_professional.id
    else:
        result = await db.execute(
            select(ProfessionalInCharge.id).where(
            ProfessionalInCharge.email == user.email
            )
        )
        existing_prof = result.scalars().first()
        if existing_prof:
            architect_id = existing_prof

    site_conditions = []
    if data.siteConditionIds:
        result = await db.execute(
            select(SiteCondition).where(SiteCondition.id.in_(data.siteConditionIds))
        )
        site_conditions = result.scalars().all()


    # Create new application
    application = PermitApplication(
        applicant_id=user_id,
        permit_type_id=data.permitTypeId,
        mmda_id=int(data.mmdaId),
        architect_id=architect_id,
        project_name=data.projectName,
        project_description=data.projectDescription,
        project_address=data.projectAddress,
        parcel_number=data.parcelNumber,
        zoning_district_id=int(data.zoningDistrictId) if data.zoningDistrictId else None,
        zoning_use_id=int(data.zoningUseId) if data.zoningUseId else None,
        estimated_cost=data.estimatedCost,
        construction_area=data.constructionArea,
        expected_start_date=data.expected_start_date,
        expected_end_date=data.expected_end_date,
        drainage_type_id=int(data.drainageTypeId) if data.drainageTypeId else None,
        previous_land_use_id = (
            data.previousLandUseId
            if data.previousLandUseId and data.previousLandUseId != "none"
            else None
        ),
        submitted_at=datetime.utcnow(),
        latitude=data.latitude,
        longitude=data.longitude,
        parcel_geometry=geojson_to_ewkt(data.parcelGeometry) if data.parcelGeometry else None,
        spatial_data=geojson_to_ewkt(data.zoningDistrictSpatial) if data.zoningDistrictSpatial else None,
        project_location=f"SRID=4326;POINT({data.longitude} {data.latitude})" if data.longitude and data.latitude else None,
        setbacks={
            "front": data.setbackFront,
            "rear": data.setbackRear,
            "left": data.setbackLeft,
            "right": data.setbackRight,
        },
        floor_areas={
            "maxHeight": data.maxHeight,
            "maxCoverage": data.maxCoverage,
            "minPlotSize": data.minPlotSize,
            "bufferZones": data.bufferZones,
            "density": data.density,
            "landscapeArea": data.landscapeArea,
            "occupantCapacity": data.occupantCapacity,
        },
        site_conditions=site_conditions,
        gis_metadata={entry["key"]: entry["value"] for entry in data.gisMetadata or []},
        fire_safety_plan=data.fireSafetyPlan,                # ✅ NEW
        waste_management_plan=data.wasteManagementPlan, 
        status=ApplicationStatus.SUBMITTED,
        application_number=f"APP-{uuid4().hex[:6].upper()}",
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)

    # 🔗 Link any successful unlinked payment
    result = await db.execute(
        select(Payment)
        .where(
            Payment.user_id == user_id,
            Payment.purpose == PaymentPurpose.PROCESSING_FEE,
            Payment.status == PaymentStatus.COMPLETED,
            Payment.application_id.is_(None)
        )
        .order_by(Payment.payment_date.desc())  # get the most recent one
        .limit(1)
    )
    payment = result.scalar_one_or_none()

    if payment:
        payment.application_id = application.id
        db.add(payment)
        await db.commit()


    # Store documents
    for doc_type_id, upload in data.documentUploads.items():
        document = ApplicationDocument(
            application_id=application.id,
            document_type_id=int(doc_type_id),
            file_path=upload.file_url,  # ✅ Match column name
            uploaded_by_id=user_id,     # ✅ Match correct foreign key
        )
        db.add(document)


    await db.commit()
    return {"id": application.id}


@router.get("/reviewer/permit/{application_id}", response_model=ReviewerPermitApplicationOut)
async def get_permit_application_for_reviewer(
    application_id: int,
    request: Request,
    db: AsyncSession = Depends(aget_db)
):
    # 1. Extract and decode JWT token to get reviewer ID
    token = request.cookies.get("auth_token")

    print("token is: ", token)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_jwt_token(token)
        reviewer_user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 2. Get the MMDA the reviewer is assigned to via committee
    mmda_query = (
        select(MMDA.id)
        .join(Committee)
        .join(CommitteeMember)
        .where(CommitteeMember.user_id == reviewer_user_id)
        .limit(1)
    )
    mmda_result = await db.execute(mmda_query)
    mmda_id = mmda_result.scalar()

    if not mmda_id:
        raise HTTPException(status_code=403, detail="Reviewer not assigned to any MMDA committee")

    # 3. Load the permit application with full relations, but only if in reviewer's MMDA
    app_query = (
        select(PermitApplication)
        .options(
            joinedload(PermitApplication.applicant).joinedload(User.profile),
            joinedload(PermitApplication.architect),
            joinedload(PermitApplication.mmda),
            joinedload(PermitApplication.permit_type),
            joinedload(PermitApplication.documents).joinedload(ApplicationDocument.document_type),
            joinedload(PermitApplication.reviews),
            joinedload(PermitApplication.inspections),
            joinedload(PermitApplication.payments),
            joinedload(PermitApplication.status_history),
            joinedload(PermitApplication.zoning_district),
            joinedload(PermitApplication.zoning_use),
            joinedload(PermitApplication.drainage_type),
            joinedload(PermitApplication.previous_land_use),
            joinedload(PermitApplication.site_conditions),
        )
        .where(
            PermitApplication.id == application_id,
            PermitApplication.mmda_id == mmda_id
        )
    )

    result = await db.execute(app_query)
    application = result.unique().scalar_one_or_none()

    if not application:
        raise HTTPException(status_code=403, detail="Access denied to this application")

    try:
        data = ReviewerPermitApplicationOut.from_orm(application).model_dump()
        # Manually serialize WKBElement spatial fields
        data["parcel_geometry"] = serialize_geom(application.parcel_geometry)
        data["spatial_data"] = serialize_geom(application.spatial_data)
        data["project_location"] = serialize_geom(application.project_location)
        return data
    except Exception as e:
        print("Serialization error:", e)
        raise HTTPException(status_code=500, detail="Response serialization failed")
    



@router.post("/reviewer/applications/{application_id}/review", response_model=ReviewerPermitApplicationOut)
async def set_under_review(
    application_id: int,
    data: UpdateReviewStatusRequest,
    request: Request,
    db: AsyncSession = Depends(aget_db)
):
    # 1. Decode JWT token from cookie
    token = request.cookies.get("auth_token")
    print("Token is: ", token)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_jwt_token(token)
        reviewer_user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 2. Get MMDA for reviewer via committee
    mmda_query = (
        select(MMDA.id)
        .join(Committee)
        .join(CommitteeMember)
        .where(CommitteeMember.user_id == reviewer_user_id)
        .limit(1)
    )
    mmda_result = await db.execute(mmda_query)
    mmda_id = mmda_result.scalar()

    if not mmda_id:
        raise HTTPException(status_code=403, detail="Reviewer not assigned to any MMDA committee")

    # 3. Load the application (must belong to reviewer's MMDA)
    app_query = (
        select(PermitApplication)
        .options(
            joinedload(PermitApplication.applicant).joinedload(User.profile),
            joinedload(PermitApplication.architect),
            joinedload(PermitApplication.mmda),
            joinedload(PermitApplication.permit_type),
            joinedload(PermitApplication.documents).joinedload(ApplicationDocument.document_type),
            joinedload(PermitApplication.reviews),
            joinedload(PermitApplication.inspections),
            joinedload(PermitApplication.payments),
            joinedload(PermitApplication.status_history),
            joinedload(PermitApplication.zoning_district),
            joinedload(PermitApplication.zoning_use),
            joinedload(PermitApplication.drainage_type),
            joinedload(PermitApplication.previous_land_use),
            joinedload(PermitApplication.site_conditions),
        )
        .where(
            PermitApplication.id == application_id,
            PermitApplication.mmda_id == mmda_id
        )
    )
    app_result = await db.execute(app_query)
    application = app_result.unique().scalar_one_or_none()

    if not application:
        raise HTTPException(status_code=403, detail="Access denied to this application")

    # 4. Save old status and update to new status
    previous_status = application.status
    application.status = data.newStatus  # e.g., ApplicationStatus.UNDER_REVIEW

    # 5. Check for existing review
    review_query = (
        select(ApplicationReview)
        .where(ApplicationReview.application_id == application_id)
        .order_by(ApplicationReview.created_at.desc())
        .limit(1)
    )
    review_result = await db.execute(review_query)
    review = review_result.scalar_one_or_none()

    if review:
        review.status = ReviewStatus.IN_PROGRESS
        review.comments = data.comments
    else:
        new_review = ApplicationReview(
            application_id=application_id,
            review_officer_id=reviewer_user_id,
            status=ReviewStatus.IN_PROGRESS,
            comments=data.comments
        )
        db.add(new_review)

    # 6. Log status change
    status_history = ApplicationStatusHistory(
        application_id=application.id,
        from_status=previous_status,
        to_status=data.newStatus,
        changed_by_id=reviewer_user_id,
        notes=data.comments
    )
    db.add(status_history)

    # 7. Commit and refresh
    await db.commit()
    await db.refresh(application)

    # 8. Serialize application safely
    try:
        data = ReviewerPermitApplicationOut.from_orm(application).model_dump()
        data["parcel_geometry"] = serialize_geom(application.parcel_geometry)
        data["spatial_data"] = serialize_geom(application.spatial_data)
        data["project_location"] = serialize_geom(application.project_location)
        return data
    except Exception as e:
        print("Serialization error:", e)
        raise HTTPException(status_code=500, detail="Response serialization failed")


@router.post("/reviewer/applications/{application_id}/submit-review")
async def submit_review(application_id: int, request: Request, db: AsyncSession = Depends(aget_db)):
    # --- Step 0: Authenticate reviewer ---
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_jwt_token(token)
        reviewer_user_id = int(payload["sub"])
    except (KeyError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid token")

    # --- Step 1: Parse input data ---
    body = await request.json()
    new_status_str = (body.get("newStatus") or "").lower()
    comments = body.get("comments")
    required_changes = body.get("requiredChanges")
    inspection_date = body.get("inspectionDate")
    inspection_notes = body.get("inspectionNotes")

    issued_at = datetime.now(timezone.utc) if new_status_str == "issued" else None

    # --- Step 2: Validate new status ---
    STATUS_MAP_REVERSE = {
        "draft": ApplicationStatus.DRAFT,
        "submitted": ApplicationStatus.SUBMITTED,
        "under_review": ApplicationStatus.UNDER_REVIEW,
        "additional_info_requested": ApplicationStatus.ADDITIONAL_INFO_REQUESTED,
        "approved": ApplicationStatus.APPROVED,
        "rejected": ApplicationStatus.REJECTED,
        "inspection_pending": ApplicationStatus.INSPECTION_PENDING,
        "inspected": ApplicationStatus.INSPECTION_COMPLETED,
        "approval_requested": ApplicationStatus.FOR_APPROVAL_OR_REJECTION,
        "issued": ApplicationStatus.ISSUED,
        "completed": ApplicationStatus.COMPLETED,
        "cancelled": ApplicationStatus.CANCELLED,
    }

    normalized_status_str = new_status_str.strip().lower().replace(" ", "_")

    new_enum_status = STATUS_MAP_REVERSE.get(normalized_status_str)
    if not new_enum_status:
        print("No New Enummeration.", new_status_str)
        raise HTTPException(status_code=400, detail=f"Invalid status: {new_status_str}")

    # --- Step 3: Determine review outcome ---
    status_to_outcome_map = {
        "approved": ReviewOutcome.APPROVED,
        "rejected": ReviewOutcome.REJECTED,
        "sent_for_approval": ReviewOutcome.NEEDS_MORE_INFO,
        "canceled": ReviewOutcome.REJECTED,
    }
    resolved_outcome = (
        ReviewOutcome.NEEDS_MORE_INFO if new_status_str == "inspection_pending"
        else status_to_outcome_map.get(new_status_str)
    )

    # --- Step 4: Insert or update review record ---
    stmt = (
        insert(ApplicationReview)
        .values(
            application_id=application_id,
            review_officer_id=reviewer_user_id,
            status=ReviewStatus.COMPLETED,
            outcome=resolved_outcome,
            comments=comments,
            requested_additional_info=required_changes or None,
        )
        .on_conflict_do_update(
            index_elements=["application_id", "review_officer_id"],
            set_={
                "status": ReviewStatus.COMPLETED,
                "outcome": resolved_outcome,
                "comments": comments,
                "requested_additional_info": required_changes or None,
            },
        )
    )
    await db.execute(stmt)

    # --- Step 5: Fetch application ---
    result = await db.execute(select(PermitApplication).where(PermitApplication.id == application_id))
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # --- Step 6: Create inspection if needed ---
    if new_status_str == "inspection_pending" and inspection_date:
        try:
            dt = datetime.fromisoformat(inspection_date.replace("Z", "+00:00"))
            inspection_dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid inspectionDate format")
        
        print("Enumeration is: ", InspectionType.INITIAL)

        inspection = Inspection(
            application_id=application_id,
            inspection_officer_id=reviewer_user_id,
            applicant_id=application.applicant_id,
            mmda_id=application.mmda_id,
            inspection_type=InspectionType.INITIAL,
            status=InspectionStatus.PENDING,
            scheduled_date=inspection_dt,
            actual_date=inspection_dt,
            notes=inspection_notes,
        )
        db.add(inspection)

    # --- Step 7: Mark review step complete ---
    step_stmt = (
        insert(ApplicationReviewStep)
        .values(
            application_id=application_id,
            reviewer_id=reviewer_user_id,
            step_name="Decision",
            completed=True,
            completed_at=datetime.utcnow(),
        )
        .on_conflict_do_update(
            index_elements=["application_id", "reviewer_id", "step_name"],
            set_={
                "completed": True,
                "completed_at": datetime.utcnow(),
                "flagged": False,
                "flag_reason": None,
                "flagged_at": None,
            },
        )
    )
    await db.execute(step_stmt)

    # --- Step 8: Update application status ---
    original_status = application.status
    update_data = {
        "status": new_enum_status,
        "updated_at": datetime.utcnow(),
    }
    if issued_at:
        update_data["approved_at"] = issued_at

    app_update_stmt = (
        update(PermitApplication)
        .where(PermitApplication.id == application_id)
        .values(**update_data)
    )
    await db.execute(app_update_stmt)

    # --- Step 9: Record status history ---
    status_history = ApplicationStatusHistory(
        application_id=application_id,
        from_status=original_status,
        to_status=new_enum_status,
        changed_by_id=reviewer_user_id,
        notes=comments,
    )
    db.add(status_history)

    # --- Finalize ---
    await db.commit()

    return {"success": True, "new_status": new_status_str}




# Track The Current Step Completed by the Reviewer 
@router.post("/reviewer/applications/{application_id}/steps/{step_name}/complete")
async def mark_step_complete(
    application_id: int,
    step_name: str,
    request: Request,
    db: AsyncSession = Depends(aget_db),
):
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_jwt_token(token)
        reviewer_user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Upsert step completion and clear any flags
    stmt = (
        insert(ApplicationReviewStep)
        .values(
            application_id=application_id,
            reviewer_id=reviewer_user_id,
            step_name=step_name,
            completed=True,
            completed_at=datetime.utcnow(),
            flagged=False,
            flag_reason=None,
            flagged_at=None,
        )
        .on_conflict_do_update(
            index_elements=["application_id", "reviewer_id", "step_name"],
            set_={
                "completed": True,
                "completed_at": datetime.utcnow(),
                "flagged": False,
                "flag_reason": None,
                "flagged_at": None,
            },
        )
    ) 

    await db.execute(stmt)
    await db.commit()

    return {"success": True, "step": step_name}



# Allow Reviewers Flag at every step 
@router.post("/reviewer/applications/{application_id}/steps/{step_name}/flag")
async def flag_step_exception(
    application_id: int,
    step_name: str,
    data: FlagStepRequest,
    request: Request,
    db: AsyncSession = Depends(aget_db),
):
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_jwt_token(token)
        reviewer_user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Ensure reviewer is part of a committee
    mmda_query = (
        select(MMDA.id)
        .join(Committee)
        .join(CommitteeMember)
        .where(CommitteeMember.user_id == reviewer_user_id)
        .limit(1)
    )
    mmda_result = await db.execute(mmda_query)
    mmda_id = mmda_result.scalar()
    if not mmda_id:
        raise HTTPException(status_code=403, detail="Reviewer not assigned to any MMDA")

    # Upsert review step (create if missing)
    stmt = insert(ApplicationReviewStep).values(
        application_id=application_id,
        reviewer_id=reviewer_user_id,
        step_name=step_name,
        flagged=True,
        flag_reason=data.reason,
        flagged_at=datetime.utcnow(),
    ).on_conflict_do_update(
        index_elements=["application_id", "reviewer_id", "step_name"],
        set_={
            "flagged": True,
            "flag_reason": data.reason,
            "flagged_at": datetime.utcnow(),
        },
    )

    await db.execute(stmt)
    await db.commit()
    return {"detail": f"Step '{step_name}' flagged with reason."}