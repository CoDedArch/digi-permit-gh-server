import traceback
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime

from app.core.constants import UserRole
from app.core.database import aget_db
from app.models.document import ApplicationDocument
from app.models.inspection import Inspection, InspectionStatus, InspectionType
from app.models.application import PermitApplication
from app.models.user import MMDA, User
from app.schemas.InspectionSchema import InspectionDetailOut, InspectionOut, InspectionRequest
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

        # Get inspection with optimized query
        stmt = (
    select(Inspection)
    .options(
        selectinload(Inspection.application).load_only(
            PermitApplication.id,
            PermitApplication.application_number,
            PermitApplication.project_name,
            # PermitApplication.project_location,
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
    )
    .where(Inspection.id == inspection_id)
)


        result = await db.execute(stmt)
        inspection = result.scalar_one_or_none()

        if not inspection:
            raise HTTPException(status_code=404, detail="Inspection not found")

        # Return response using from_orm
        return InspectionDetailOut.from_orm(inspection)

    except HTTPException:
        raise  # Re-raise known exceptions
    except Exception as e:
        traceback.print_exc()  # Log full traceback for debugging
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
