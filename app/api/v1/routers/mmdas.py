from datetime import datetime, time, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import joinedload
from app.core.constants import ApplicationStatus
from app.core.database import aget_db
from app.core.security import decode_jwt_token
from app.models.application import PermitApplication
from app.models.document import PermitTypeModel
from app.models.user import MMDA, Committee, Department, DepartmentStaff, User
from app.schemas.User import CommitteeBase, DepartmentBase
from app.schemas.mmda import MMDABase  # You’ll need this schema

router = APIRouter(
    prefix="/mmdas",
    tags=["mmdas"]
)

@router.get("/", response_model=List[MMDABase])
async def get_all_mmdas(db: AsyncSession = Depends(aget_db)):
    result = await db.execute(select(MMDA))
    mmdas = result.scalars().all()
    return mmdas

@router.get("/{mmda_id}/departments", response_model=List[DepartmentBase])
async def get_mmda_departments(mmda_id: int, db: AsyncSession = Depends(aget_db)):
    result = await db.execute(select(Department).where(Department.mmda_id == mmda_id))
    departments = result.scalars().all()
    return departments

@router.get("/{mmda_id}/committees", response_model=List[CommitteeBase])
async def get_mmda_committees(mmda_id: int, db: AsyncSession = Depends(aget_db)):
    result = await db.execute(select(Committee).where(Committee.mmda_id == mmda_id))
    committees = result.scalars().all()
    return committees


@router.get("/dashboard/reviewer-stats")
async def get_reviewer_stats(request: Request, db: AsyncSession = Depends(aget_db)):
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

    # Get current date and time
    now = datetime.now()
    today_start = datetime.combine(now.date(), time.min)
    today_end = datetime.combine(now.date(), time.max)

    # 1. Pending Review (submitted status)
    pending_result = await db.execute(
        select(func.count(PermitApplication.id))
        .filter(PermitApplication.mmda_id == mmda_id)
        .filter(PermitApplication.status == ApplicationStatus.SUBMITTED)
    )
    pending_review = pending_result.scalar_one() or 0

    # 2. Overdue applications - fixed calculation
    # First get all permits with their standard duration
    permits_with_duration = await db.execute(
        select(
            PermitApplication.id,
            PermitApplication.status,
            PermitApplication.submitted_at,
            PermitTypeModel.standard_duration_days
        )
        .join(PermitTypeModel)
        .filter(PermitApplication.mmda_id == mmda_id)
    )
    
    overdue_count = 0
    for permit in permits_with_duration:
        if not permit.submitted_at:
            continue
            
        time_in_review = now - permit.submitted_at
        standard_duration = permit.standard_duration_days
        
        # Submitted for more than 2 days
        if (permit.status == ApplicationStatus.SUBMITTED and 
            time_in_review > timedelta(days=2)):
            overdue_count += 1
        # Under review for more than half standard duration
        elif (permit.status == ApplicationStatus.UNDER_REVIEW and 
              time_in_review > timedelta(days=standard_duration/2)):
            overdue_count += 1
        # No decision after full standard duration
        elif (permit.status in [ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW] and 
              time_in_review > timedelta(days=standard_duration)):
            overdue_count += 1

    # 3. Completed Today (approved or rejected today)
    completed_today_result = await db.execute(
        select(func.count(PermitApplication.id))
        .filter(PermitApplication.mmda_id == mmda_id)
        .filter(
            or_(
                PermitApplication.status == ApplicationStatus.APPROVED,
                PermitApplication.status == ApplicationStatus.REJECTED
            )
        )
        .filter(
            PermitApplication.updated_at.between(today_start, today_end)
        )
    )
    completed_today = completed_today_result.scalar_one() or 0

    # 4. Average Review Time (for completed applications)
    avg_review_time_result = await db.execute(
        select(
            func.avg(
                func.extract('epoch', PermitApplication.updated_at - PermitApplication.submitted_at) / 86400  # Convert seconds to days
            )
        )
        .filter(PermitApplication.mmda_id == mmda_id)
        .filter(
            or_(
                PermitApplication.status == ApplicationStatus.APPROVED,
                PermitApplication.status == ApplicationStatus.REJECTED
            )
        )
        .filter(PermitApplication.submitted_at.isnot(None))
    )
    avg_review_days = avg_review_time_result.scalar_one() or 0
    avg_review_days_rounded = round(float(avg_review_days), 1) if avg_review_days else 0

    return {
        "pending_review": pending_review,
        "overdue": overdue_count,
        "completed_today": completed_today,
        "avg_review_time_days": avg_review_days_rounded
    }


@router.get("/dashboard/reviewer-queue")
async def get_reviewer_queue(request: Request, db: AsyncSession = Depends(aget_db)):
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

    # Get current date and time
    now = datetime.now()

    # First fetch all relevant applications with their standard durations
    result = await db.execute(
        select(
            PermitApplication.id,
            PermitApplication.application_number,
            PermitTypeModel.name.label("permit_type"),
            User.first_name,
            User.last_name,
            PermitApplication.submitted_at,
            PermitApplication.status,
            PermitTypeModel.standard_duration_days
        )
        .join(PermitTypeModel, PermitApplication.permit_type_id == PermitTypeModel.id)
        .join(User, PermitApplication.applicant_id == User.id)
        .filter(PermitApplication.mmda_id == mmda_id)
        .filter(
            or_(
                PermitApplication.status == ApplicationStatus.SUBMITTED,
                PermitApplication.status == ApplicationStatus.UNDER_REVIEW
            )
        )
    )

    # Get all rows from the result
    applications = result.all()
    print("APPLICATIONS ARE", applications)

    queue_data = []
    for app in applications:
        # Handle cases where submitted_at is None
        if app.submitted_at is None:
            days_in_queue = 0  # or some default value
            submitted_date = now  # or some default date
        else:
            days_in_queue = (now - app.submitted_at).days
            submitted_date = app.submitted_at

        standard_duration = app.standard_duration_days
        
        # Calculate priority - modified to handle cases with no submission date
        if app.submitted_at is None:
            priority = "medium"  # default priority for applications without submission date
        elif (app.status == ApplicationStatus.SUBMITTED and days_in_queue > 2):
            priority = "high"
        elif (app.status == ApplicationStatus.UNDER_REVIEW and 
              days_in_queue > (standard_duration / 2)):
            priority = "high"
        elif days_in_queue > standard_duration:
            priority = "high"
        elif (app.status == ApplicationStatus.UNDER_REVIEW and 
              days_in_queue > (standard_duration / 4)):
            priority = "medium"
        else:
            priority = "low"

        queue_data.append({
            "permit_no": app.application_number,
            "type": app.permit_type,
            "applicant": f"{app.first_name} {app.last_name}",
            "days_in_queue": days_in_queue,
            "priority": priority,
            "permit_id": app.id,
            "has_submission_date": app.submitted_at is not None  # for debugging
        })
        
    # Sort by priority (high first) and then by days in queue (most days first)
    queue_data.sort(key=lambda x: (
        -1 if x["priority"] == "high" else 
        -0.5 if x["priority"] == "medium" else 0,
        -x["days_in_queue"]
    ))

    print("QUEUE IS", queue_data)

    return queue_data[:10]  # Return top 10 priority applications