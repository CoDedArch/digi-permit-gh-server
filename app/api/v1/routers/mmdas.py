from datetime import datetime, time, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import joinedload
from app.core.constants import ApplicationStatus, InspectionStatus, ReviewStatus
from app.core.database import aget_db
from app.core.security import decode_jwt_token
from app.models.application import PermitApplication
from app.models.document import PermitTypeModel
from app.models.inspection import Inspection
from app.models.review import ApplicationReview
from app.models.user import MMDA, Committee, CommitteeMember, Department, DepartmentStaff, User
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
async def get_reviewer_stats(
    request: Request, 
    db: AsyncSession = Depends(aget_db)
):
    """Get statistics for reviewer dashboard, filtered by department and committee assignments"""
    # Authentication
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = decode_jwt_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Get reviewer's department and committee assignments
    staff_result = await db.execute(
        select(DepartmentStaff)
        .join(Department)
        .options(
            joinedload(DepartmentStaff.department),
            joinedload(DepartmentStaff.committee_memberships)
            .joinedload(CommitteeMember.committee)
        )
        .where(DepartmentStaff.user_id == user_id)
    )
    staff = staff_result.scalars().first()
    
    if not staff:
        raise HTTPException(status_code=403, detail="User is not a staff member")

    now = datetime.now()
    today_start = datetime.combine(now.date(), time.min)
    today_end = datetime.combine(now.date(), time.max)

    # Base filter for applications this reviewer should see
    base_filter = and_(
        PermitApplication.mmda_id == staff.department.mmda_id,
        PermitApplication.department_id == staff.department_id
    )

    if not staff.is_head:
        # Regular reviewers only see applications from their committees
        committee_ids = [cm.committee.id for cm in staff.committee_memberships]
        base_filter = and_(
            base_filter,
            or_(
                PermitApplication.committee_id.in_(committee_ids),
                PermitApplication.committee_id.is_(None)  # Department-only reviews
            )
        )

    # 1. Pending Reviews (filtered by department/committee)
    pending_result = await db.execute(
        select(func.count(PermitApplication.id))
        .where(
            base_filter,
            PermitApplication.status == ApplicationStatus.SUBMITTED
        )
    )
    pending_review = pending_result.scalar_one() or 0

    # 2. Overdue Applications (filtered by department/committee)
    permits_with_duration = await db.execute(
        select(
            PermitApplication.id,
            PermitApplication.status,
            PermitApplication.submitted_at,
            PermitTypeModel.standard_duration_days
        )
        .join(PermitTypeModel)
        .where(base_filter)
    )

    overdue_count = 0
    for permit in permits_with_duration:
        if not permit.submitted_at:
            continue
            
        time_in_review = now - permit.submitted_at
        standard_duration = permit.standard_duration_days or 30  # Default 30 days

        if (permit.status == ApplicationStatus.SUBMITTED and time_in_review > timedelta(days=2)):
            overdue_count += 1
        elif (permit.status == ApplicationStatus.UNDER_REVIEW and 
              time_in_review > timedelta(days=standard_duration / 2)):
            overdue_count += 1
        elif time_in_review > timedelta(days=standard_duration):
            overdue_count += 1

    # 3. Completed Today - Department/Committee scope
    completed_today_result = await db.execute(
        select(func.count(PermitApplication.id))
        .where(
            base_filter,
            or_(
                PermitApplication.status == ApplicationStatus.APPROVED,
                PermitApplication.status == ApplicationStatus.REJECTED
            ),
            PermitApplication.updated_at.between(today_start, today_end)
        )
    )
    completed_today = completed_today_result.scalar_one() or 0

    # 4. Reviewer's Completed Today
    completed_today_reviewer_result = await db.execute(
        select(func.count())
        .select_from(ApplicationReview)
        .join(PermitApplication, ApplicationReview.application_id == PermitApplication.id)
        .where(
            ApplicationReview.review_officer_id == user_id,
            ApplicationReview.status == ReviewStatus.COMPLETED,
            ApplicationReview.updated_at.between(today_start, today_end),
            base_filter  # Ensure it's within reviewer's scope
        )
    )
    completed_today_reviewer = completed_today_reviewer_result.scalar_one() or 0

    # 5. Average Review Time - Department/Committee scope
    avg_review_time_result = await db.execute(
        select(
            func.avg(
                func.extract('epoch', PermitApplication.updated_at - PermitApplication.submitted_at) / 86400
            )
        )
        .where(
            base_filter,
            or_(
                PermitApplication.status == ApplicationStatus.APPROVED,
                PermitApplication.status == ApplicationStatus.REJECTED
            ),
            PermitApplication.submitted_at.isnot(None)
        )
    )
    avg_review_time = avg_review_time_result.scalar_one() or 0
    avg_review_time_rounded = round(float(avg_review_time), 1) if avg_review_time else 0

    # 6. Reviewer's Average Review Time
    avg_reviewer_time_result = await db.execute(
        select(
            func.avg(
                func.extract('epoch', ApplicationReview.updated_at - ApplicationReview.created_at) / 86400
            )
        )
        .join(PermitApplication, ApplicationReview.application_id == PermitApplication.id)
        .where(
            ApplicationReview.review_officer_id == user_id,
            ApplicationReview.status == ReviewStatus.COMPLETED,
            base_filter  # Ensure it's within reviewer's scope
        )
    )
    avg_reviewer_time = avg_reviewer_time_result.scalar_one() or 0
    avg_reviewer_time_rounded = round(float(avg_reviewer_time), 1) if avg_reviewer_time else 0

    return {
        "pending_review": pending_review,
        "overdue": overdue_count,
        "completed_today": completed_today,
        "completed_today_reviewer": completed_today_reviewer,
        "avg_review_time_days": avg_review_time_rounded,
        "avg_review_time_days_reviewer": avg_reviewer_time_rounded,
        # "department": staff.department.name,
        # "is_department_head": staff.is_head,
        # "committee_count": len(staff.committee_memberships)
    }



@router.get("/dashboard/reviewer-queue")
async def get_reviewer_queue(
    request: Request, 
    db: AsyncSession = Depends(aget_db),
    status: Optional[ApplicationStatus] = None
):
    """
    Get applications in the reviewer's queue, filtered by their department and committee assignments.
    """
    # Authentication
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = decode_jwt_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Get reviewer's department and committee assignments
    staff_result = await db.execute(
        select(DepartmentStaff)
        .join(Department)
        .options(
            joinedload(DepartmentStaff.department)
            .joinedload(Department.mmda),
            joinedload(DepartmentStaff.committee_memberships)
            .joinedload(CommitteeMember.committee)
        )
        .where(DepartmentStaff.user_id == user_id)
    )
    staff = staff_result.scalars().first()
    
    if not staff:
        raise HTTPException(status_code=403, detail="User is not a staff member")

    # Get current date and time
    now = datetime.now()

    # Base query with all necessary joins
    query = (
        select(
            PermitApplication.id,
            PermitApplication.application_number,
            PermitTypeModel.name.label("permit_type"),
            User.first_name,
            User.last_name,
            PermitApplication.submitted_at,
            PermitApplication.created_at,
            PermitApplication.status,
            PermitTypeModel.standard_duration_days,
            Department.name.label("department_name"),
            Committee.name.label("committee_name")
        )
        .join(PermitTypeModel, PermitApplication.permit_type_id == PermitTypeModel.id)
        .join(User, PermitApplication.applicant_id == User.id)
        .join(Department, PermitApplication.department_id == Department.id)
        .join(Committee, PermitApplication.committee_id == Committee.id)
        .where(PermitApplication.mmda_id == staff.department.mmda_id)
    )

    # Filter by status if provided
    if status:
        query = query.where(PermitApplication.status == status)
    else:
        query = query.where(
            or_(
                PermitApplication.status == ApplicationStatus.SUBMITTED,
                PermitApplication.status == ApplicationStatus.UNDER_REVIEW
            )
        )

    # Filter by reviewer's department and committees
    if staff.is_head:
        # Department heads see all applications in their department
        query = query.where(PermitApplication.department_id == staff.department_id)
    else:
        # Regular reviewers see applications where:
        # 1. They're assigned to the department AND
        # 2. They're members of the committee OR it's a department-level review
        committee_ids = [cm.committee.id for cm in staff.committee_memberships]
        query = query.where(
            and_(
                PermitApplication.department_id == staff.department_id,
                or_(
                    PermitApplication.committee_id.in_(committee_ids),
                    PermitApplication.committee_id.is_(None)  # Department-only reviews
                )
            )
        )

    # Execute the query
    result = await db.execute(query)
    applications = result.all()

    # Process applications into queue data
    queue_data = []
    for app in applications:
        # Calculate days in queue
        submitted_date = app.submitted_at or app.created_at
        days_in_queue = (now - submitted_date).days
        standard_duration = app.standard_duration_days or 30  # Default 30 days if not set

        # Determine priority
        if app.status == ApplicationStatus.SUBMITTED and days_in_queue > 2:
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
            "has_submission_date": submitted_date.isoformat(),
        })

    # Sort by priority (high first) and days in queue (descending)
    queue_data.sort(key=lambda x: (
        -1 if x["priority"] == "high" else 
        -0.5 if x["priority"] == "medium" else 0,
        -x["days_in_queue"]
    ))

    return queue_data[:100]  # Return top 100 by default


@router.get("/dashboard/inspection-stats")
async def get_inspection_stats(request: Request, db: AsyncSession = Depends(aget_db)):
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = decode_jwt_token(token)
        user_id = int(payload.get("sub"))

        # Get the inspector's MMDA info
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
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    now = datetime.now()
    today_start = datetime.combine(now.date(), time.min)
    today_end = datetime.combine(now.date(), time.max)
    thirty_days_ago = now - timedelta(days=30)

    # 1. Scheduled Today (assigned to this officer)
    scheduled_today_result = await db.execute(
        select(func.count(Inspection.id))
        .filter(Inspection.mmda_id == mmda_id)
        .filter(Inspection.inspection_officer_id == user_id)
        .filter(Inspection.scheduled_date.between(today_start, today_end))
        .filter(Inspection.status == InspectionStatus.SCHEDULED)
    )
    scheduled_today = scheduled_today_result.scalar_one() or 0

    # 2. Pending Reports (inspections done but report not submitted)
    pending_reports_result = await db.execute(
        select(func.count(Inspection.id))
        .filter(Inspection.mmda_id == mmda_id)
        .filter(Inspection.inspection_officer_id == user_id)
        .filter(Inspection.actual_date.isnot(None))
        .filter(Inspection.status == InspectionStatus.COMPLETED)
        .filter(Inspection.findings.is_(None))  # No findings means report not submitted
    )
    pending_reports = pending_reports_result.scalar_one() or 0

    # 3. Violations Found (in this MMDA, last 30 days)
    violations_result = await db.execute(
        select(func.count(Inspection.id))
        .filter(Inspection.mmda_id == mmda_id)
        .filter(Inspection.inspection_officer_id == user_id)
        .filter(Inspection.actual_date >= thirty_days_ago)
        .filter(Inspection.violations_found.isnot(None))
    )
    violations_found = violations_result.scalar_one() or 0

    # 4. Inspections In Progress
    in_progress_result = await db.execute(
        select(func.count(Inspection.id))
        .filter(Inspection.mmda_id == mmda_id)
        .filter(Inspection.inspection_officer_id == user_id)
        .filter(Inspection.status == InspectionStatus.IN_PROGRESS)
    )
    in_progress = in_progress_result.scalar_one() or 0

    # 5. Completed This Week
    week_start = now - timedelta(days=now.weekday())
    completed_week_result = await db.execute(
        select(func.count(Inspection.id))
        .filter(Inspection.mmda_id == mmda_id)
        .filter(Inspection.inspection_officer_id == user_id)
        .filter(Inspection.status == InspectionStatus.COMPLETED)
        .filter(Inspection.actual_date >= week_start)
    )
    completed_week = completed_week_result.scalar_one() or 0

    # 6. Average Inspection Duration (last 30 days)
    avg_duration_result = await db.execute(
        select(
            func.avg(
                func.extract('epoch', Inspection.actual_date - Inspection.scheduled_date) / 3600  # in hours
            )
        )
        .filter(Inspection.mmda_id == mmda_id)
        .filter(Inspection.inspection_officer_id == user_id)
        .filter(Inspection.status == InspectionStatus.COMPLETED)
        .filter(Inspection.actual_date >= thirty_days_ago)
        .filter(Inspection.scheduled_date.isnot(None))
    )
    avg_duration_hours = round(avg_duration_result.scalar_one() or 0, 1)

    # 7. Reinspection Rate
    reinspection_result = await db.execute(
        select(func.count(Inspection.id))
        .filter(Inspection.mmda_id == mmda_id)
        .filter(Inspection.inspection_officer_id == user_id)
        .filter(Inspection.is_reinspection == True)
        .filter(Inspection.actual_date >= thirty_days_ago)
    )
    reinspections = reinspection_result.scalar_one() or 0

    total_inspections_result = await db.execute(
        select(func.count(Inspection.id))
        .filter(Inspection.mmda_id == mmda_id)
        .filter(Inspection.inspection_officer_id == user_id)
        .filter(Inspection.actual_date >= thirty_days_ago)
    )
    total_inspections = total_inspections_result.scalar_one() or 1  # Avoid division by zero

    reinspection_rate = round((reinspections / total_inspections) * 100, 1)

    return {
        "scheduled_today": scheduled_today,
        "pending_reports": pending_reports,
        "violations_found": violations_found,
        "in_progress": in_progress,
        "completed_week": completed_week,
        "avg_duration_hours": avg_duration_hours,
        "reinspection_rate": reinspection_rate,
        "total_inspections": total_inspections,
    }


@router.get("/inspections/dashboard/inspector-queue")
async def get_inspector_queue(request: Request, db: AsyncSession = Depends(aget_db)):
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = decode_jwt_token(token)
        user_id = int(payload.get("sub"))
        
        # Get the inspector's department and MMDA info
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

    # Fetch inspections assigned to this officer
    result = await db.execute(
        select(
            Inspection.id,
            PermitApplication.application_number.label("permit_no"),
            PermitApplication.project_address.label("address"),
            PermitTypeModel.name.label("permit_type"),
            User.first_name,
            User.last_name,
            Inspection.scheduled_date,
            Inspection.status,
            Inspection.inspection_type
        )
        .join(PermitApplication, Inspection.application_id == PermitApplication.id)
        .join(PermitTypeModel, PermitApplication.permit_type_id == PermitTypeModel.id)
        .join(User, PermitApplication.applicant_id == User.id)
        .filter(Inspection.mmda_id == mmda_id)
        .filter(Inspection.inspection_officer_id == user_id)
        .filter(Inspection.status.in_([
            InspectionStatus.SCHEDULED,
            InspectionStatus.IN_PROGRESS,
            InspectionStatus.PENDING
        ]))
        .order_by(Inspection.scheduled_date.asc())
    )

    inspections = result.all()

    queue_data = []
    for insp in inspections:
        # Calculate days until due (negative if overdue)
        days_until_due = 0
        if insp.scheduled_date:
            days_until_due = (insp.scheduled_date.date() - now.date()).days

        # Calculate priority
        if insp.status == InspectionStatus.IN_PROGRESS:
            priority = "high"
        elif insp.status == InspectionStatus.SCHEDULED:
            if days_until_due < 0:  # Overdue
                priority = "high"
            elif days_until_due <= 1:  # Due today or tomorrow
                priority = "medium"
            else:
                priority = "low"
        else:  # Pending
            priority = "low"

        # Format scheduled time if available
        scheduled_time = insp.scheduled_date.strftime("%I:%M %p") if insp.scheduled_date else "Not scheduled"

        queue_data.append({
            "id": insp.id,
            "permit_no": insp.permit_no,
            "address": insp.address,
            "type": insp.permit_type,
            "scheduled_time": scheduled_time,
            "status": insp.status.value,
            "days_until_due": days_until_due,
            "priority": priority,
            "applicant": f"{insp.first_name} {insp.last_name}",
            "inspection_type": insp.inspection_type.value if insp.inspection_type else None
        })
        
    # Sort by priority (high first) and then by days until due (closest first)
    queue_data.sort(key=lambda x: (
        -1 if x["priority"] == "high" else 
        -0.5 if x["priority"] == "medium" else 0,
        x["days_until_due"]
    ))

    return queue_data[:10]  # Return top 10 priority inspections


# Admin Dashboard Endpoints

@router.get("/dashboard/admin-stats")
async def get_admin_stats(request: Request, db: AsyncSession = Depends(aget_db)):
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
            .options(joinedload(DepartmentStaff.department).joinedload(Department.mmda))
            .filter(DepartmentStaff.user_id == user_id)
        )
        staff = staff_result.scalars().first()

        if not staff:
            raise HTTPException(status_code=403, detail="User is not a staff member")

        mmda_id = staff.department.mmda_id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    now = datetime.now()
    today_start = datetime.combine(now.date(), time.min)
    today_end = datetime.combine(now.date(), time.max)

   # Users who applied to this MMDA
    applicant_ids_result = await db.execute(
        select(PermitApplication.applicant_id)
        .filter(PermitApplication.mmda_id == mmda_id)
        .distinct()
    )
    applicant_ids = {row[0] for row in applicant_ids_result.fetchall()}

    # Users who are staff in this MMDA
    staff_ids_result = await db.execute(
        select(DepartmentStaff.user_id)
        .join(Department)
        .filter(Department.mmda_id == mmda_id)
    )
    staff_ids = {row[0] for row in staff_ids_result.fetchall()}

    # Combine and count unique users
    unique_user_ids = applicant_ids.union(staff_ids)
    total_users = len(unique_user_ids)


    # 2. Active Applications
    active_applications_result = await db.execute(
        select(func.count(PermitApplication.id))
        .filter(PermitApplication.mmda_id == mmda_id)
        .filter(
            PermitApplication.status.in_([
                ApplicationStatus.SUBMITTED,
                ApplicationStatus.UNDER_REVIEW
            ])
        )
    )
    active_applications = active_applications_result.scalar_one() or 0

    # 3. Average Processing Time
    avg_processing_result = await db.execute(
        select(
            func.avg(
                func.extract('epoch', PermitApplication.updated_at - PermitApplication.submitted_at) / 86400
            )
        )
        .filter(PermitApplication.mmda_id == mmda_id)
        .filter(
            PermitApplication.status.in_([
                ApplicationStatus.APPROVED,
                ApplicationStatus.REJECTED
            ])
        )
        .filter(PermitApplication.submitted_at.isnot(None))
    )
    avg_processing_time = avg_processing_result.scalar_one() or 0
    avg_processing_time_rounded = round(float(avg_processing_time), 1) if avg_processing_time else 0

    # 4. System Health (based on processing efficiency)
    overdue_result = await db.execute(
        select(func.count(PermitApplication.id))
        .join(PermitTypeModel)
        .filter(PermitApplication.mmda_id == mmda_id)
        .filter(
            PermitApplication.status.in_([
                ApplicationStatus.SUBMITTED,
                ApplicationStatus.UNDER_REVIEW
            ])
        )
        .filter(
            func.extract('epoch', now - PermitApplication.submitted_at) / 86400 
            > PermitTypeModel.standard_duration_days
        )
    )
    overdue_count = overdue_result.scalar_one() or 0
    
    system_health = max(0, 100 - (overdue_count * 5)) if active_applications > 0 else 100

    # 5. Pending Reviews
    pending_reviews_result = await db.execute(
        select(func.count(PermitApplication.id))
        .filter(PermitApplication.mmda_id == mmda_id)
        .filter(PermitApplication.status == ApplicationStatus.SUBMITTED)
    )
    pending_reviews = pending_reviews_result.scalar_one() or 0

    # 6. Active Staff
    active_staff_result = await db.execute(
        select(func.count(DepartmentStaff.user_id))
        .join(Department)
        .filter(Department.mmda_id == mmda_id)
    )
    active_staff = active_staff_result.scalar_one() or 0

    # 7. Status Distribution
    status_distribution_result = await db.execute(
        select(
            PermitApplication.status,
            func.count(PermitApplication.id)
        )
        .filter(PermitApplication.mmda_id == mmda_id)
        .group_by(PermitApplication.status)
    )
    
    status_distribution = {
        "submitted": 0,
        "under_review": 0,
        "approved": 0,
        "rejected": 0
    }
    
    for status, count in status_distribution_result:
        status_key = status.value if hasattr(status, "value") else status
        if status_key in status_distribution:
            status_distribution[status_key] = count

    # 8. Department Performance
    department_performance_result = await db.execute(
        select(
            Department.name,
            func.count(PermitApplication.id).label("completed_count"),
            func.avg(
                func.extract('epoch', PermitApplication.updated_at - PermitApplication.submitted_at) / 86400
            ).label("avg_time")
        )
        .join(PermitApplication, PermitApplication.mmda_id == Department.mmda_id, isouter=True)
        .filter(Department.mmda_id == mmda_id)
        .filter(
            or_(
                PermitApplication.status.in_([
                    ApplicationStatus.APPROVED,
                    ApplicationStatus.REJECTED
                ]),
                PermitApplication.id.is_(None)
            )
        )
        .group_by(Department.id, Department.name)
    )

    department_performance = []
    total_completed = 0
    for dept_name, completed_count, avg_time in department_performance_result:
        completed_count = completed_count or 0
        avg_time = round(float(avg_time), 1) if avg_time else 0
        total_completed += completed_count
        
        department_performance.append({
            "name": dept_name,
            "completed_applications": completed_count,
            "avg_processing_time": avg_time
        })

    return {
        "total_users": total_users,
        "active_applications": active_applications,
        "avg_processing_time_days": avg_processing_time_rounded,
        "system_health_percentage": system_health,
        "pending_reviews": pending_reviews,
        "overdue_applications": overdue_count,
        "active_staff": active_staff,
        "status_distribution": status_distribution,
        "department_performance": department_performance,
        "total_completed_applications": total_completed,
    }


@router.get("/dashboard/recent-activities")
async def get_recent_activities(request: Request, db: AsyncSession = Depends(aget_db)):
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    print("Token is Authenticated")
    try:
        payload = decode_jwt_token(token)
        user_id = int(payload.get("sub"))
        
        # Get the admin's MMDA
        staff_result = await db.execute(
            select(DepartmentStaff)
            .options(joinedload(DepartmentStaff.department).joinedload(Department.mmda))
            .filter(DepartmentStaff.user_id == user_id)
        )
        staff = staff_result.scalars().first()
        if not staff:
            raise HTTPException(status_code=403, detail="User is not a staff member")
        mmda_id = staff.department.mmda_id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    print("Out of Verification related Staff")

    # Get recent activities within the MMDA (last 24 hours)
    recent_time = datetime.now() - timedelta(hours=24)
    activities = []
    
    # Recent application submissions
    recent_apps_result = await db.execute(
        select(
            PermitApplication.created_at,
            PermitApplication.project_name,
            User.first_name,
            User.last_name
        )
        .join(User, PermitApplication.applicant_id == User.id)
        .filter(PermitApplication.mmda_id == mmda_id)
        .filter(PermitApplication.created_at >= recent_time)
        .order_by(PermitApplication.created_at.desc())
        .limit(10)
    )
    
    for created_at, project_name, first_name, last_name in recent_apps_result:
        time_diff = datetime.now() - created_at
        time_ago = format_time_ago(time_diff)
        activities.append({
            "id": len(activities) + 1,
            "user_name": f"{first_name} {last_name}",
            "action": f"Submitted application for {project_name}",
            "time_ago": time_ago,
            "activity_type": "application_action"
        })
    
    # Recent reviews completed
    recent_reviews_result = await db.execute(
        select(
            ApplicationReview.updated_at,
            PermitApplication.project_name,
            User.first_name,
            User.last_name,
            ApplicationReview.status
        )
        .join(PermitApplication, ApplicationReview.application_id == PermitApplication.id)
        .join(User, ApplicationReview.review_officer_id == User.id)
        .filter(PermitApplication.mmda_id == mmda_id)
        .filter(ApplicationReview.updated_at >= recent_time)
        .filter(ApplicationReview.status == ReviewStatus.COMPLETED)
        .order_by(ApplicationReview.updated_at.desc())
        .limit(10)
    )
    
    for updated_at, project_name, first_name, last_name, status in recent_reviews_result:
        time_diff = datetime.now() - updated_at
        time_ago = format_time_ago(time_diff)
        activities.append({
            "id": len(activities) + 1,
            "user_name": f"{first_name} {last_name}",
            "action": f"Reviewed application for {project_name} - {status.replace('_', ' ').title()}",
            "time_ago": time_ago,
            "activity_type": "user_action"
        })
    
    # Recent system actions (status changes, approvals, etc.)
    recent_status_changes_result = await db.execute(
        select(
            PermitApplication.updated_at,
            PermitApplication.project_name,
            PermitApplication.status,
            User.first_name,
            User.last_name
        )
        .join(User, PermitApplication.applicant_id == User.id)
        .filter(PermitApplication.mmda_id == mmda_id)
        .filter(PermitApplication.updated_at >= recent_time)
        .filter(PermitApplication.status.in_([
            ApplicationStatus.APPROVED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.UNDER_REVIEW
        ]))
        .order_by(PermitApplication.updated_at.desc())
        .limit(10)
    )
    
    for updated_at, project_name, status, first_name, last_name in recent_status_changes_result:
        time_diff = datetime.now() - updated_at
        time_ago = format_time_ago(time_diff)
        activities.append({
            "id": len(activities) + 1,
            "user_name": "System",
            "action": f"Application for {project_name} by {first_name} {last_name} - {status.replace('_', ' ').title()}",
            "time_ago": time_ago,
            "activity_type": "system_action"
        })
    
    # Sort all activities by most recent first
    activities.sort(key=lambda x: x["time_ago"], reverse=False)  # Assuming time_ago is sortable
    
    # Limit to 20 most recent activities and ensure unique IDs
    activities = activities[:20]
    for i, activity in enumerate(activities, 1):
        activity["id"] = i
    
    return activities


def format_time_ago(time_diff: timedelta) -> str:
    """Format time difference into human-readable string"""
    total_seconds = int(time_diff.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds}s ago"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes}m ago"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        return f"{hours}h ago"
    else:
        days = total_seconds // 86400
        return f"{days}d ago"