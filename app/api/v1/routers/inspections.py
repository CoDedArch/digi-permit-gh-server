from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from datetime import datetime

from app.core.database import aget_db
from app.models.inspection import Inspection, InspectionStatus, InspectionType
from app.models.application import PermitApplication
from app.models.user import User
from app.schemas.InspectionSchema import InspectionDetailOut, InspectionOut, InspectionRequest
from app.core.security import decode_jwt_token  # make sure this function exists

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
    db: AsyncSession = Depends(aget_db),
):
    try:
        result = await db.execute(
            select(Inspection)
            .options(
                joinedload(Inspection.application),
                joinedload(Inspection.inspection_officer),
                joinedload(Inspection.applicant),
                joinedload(Inspection.mmda),
            )
            .where(Inspection.id == inspection_id)
        )
        inspection = result.scalar_one_or_none()

        if not inspection:
            raise HTTPException(status_code=404, detail="Inspection not found")

        return inspection  # FastAPI will automatically use your Pydantic model
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
