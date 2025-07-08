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



@router.get("/user", response_model=list[InspectionOut])
async def get_user_inspections(
    request: Request,
    db: AsyncSession = Depends(aget_db),
):
    # Extract and decode token
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        decoded = decode_jwt_token(token)
        user_id = int(decoded.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Query for inspections by applicant ID
    result = await db.execute(
        select(Inspection)
        .options(joinedload(Inspection.application))
        .where(Inspection.applicant_id == user_id)
    )
    inspections = result.scalars().all()
    return inspections

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
