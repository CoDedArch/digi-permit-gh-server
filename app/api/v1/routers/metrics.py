from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta

from app.core.constants import ReviewStatus
from app.core.database import aget_db
from app.models.review import ApplicationReview, ApplicationReviewStep
from app.core.security import decode_jwt_token

router = APIRouter(
    prefix="/metrics",
    tags=["metrics"]
)


@router.get("/reviewer/metrics")
async def get_reviewer_metrics(
    request: Request,
    db: AsyncSession = Depends(aget_db),
):
    # Authenticate reviewer
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_jwt_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    now = datetime.now()
    today_start = datetime.combine(now.date(), datetime.min.time())
    today_end = datetime.combine(now.date(), datetime.max.time())

    week_start = today_start - timedelta(days=today_start.weekday())  # Monday
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

    month_start = datetime(now.year, now.month, 1)
    month_end = datetime(now.year, now.month + 1, 1) if now.month < 12 else datetime(now.year + 1, 1, 1)

    year_start = datetime(now.year, 1, 1)
    year_end = datetime(now.year + 1, 1, 1)

    # Base query: only completed reviews
    completed_reviews_query = select(ApplicationReview).where(
        ApplicationReview.review_officer_id == user_id,
        ApplicationReview.status == ReviewStatus.COMPLETED
    )

    # Metrics

    total_assigned = await db.scalar(
        select(func.count()).select_from(ApplicationReview).where(
            ApplicationReview.review_officer_id == user_id
        )
    )

    total_completed = await db.scalar(
        select(func.count()).select_from(completed_reviews_query.subquery())
    )

    pending = await db.scalar(
        select(func.count()).select_from(ApplicationReview).where(
            ApplicationReview.review_officer_id == user_id,
            ApplicationReview.status == ReviewStatus.PENDING
        )
    )

    completed_today = await db.scalar(
        select(func.count()).select_from(ApplicationReview).where(
            ApplicationReview.review_officer_id == user_id,
            ApplicationReview.status == ReviewStatus.COMPLETED,
            ApplicationReview.updated_at.between(today_start, today_end)
        )
    )

    completed_this_week = await db.scalar(
        select(func.count()).select_from(ApplicationReview).where(
            ApplicationReview.review_officer_id == user_id,
            ApplicationReview.status == ReviewStatus.COMPLETED,
            ApplicationReview.updated_at.between(week_start, week_end)
        )
    )

    completed_this_month = await db.scalar(
        select(func.count()).select_from(ApplicationReview).where(
            ApplicationReview.review_officer_id == user_id,
            ApplicationReview.status == ReviewStatus.COMPLETED,
            ApplicationReview.updated_at.between(month_start, month_end)
        )
    )

    completed_this_year = await db.scalar(
        select(func.count()).select_from(ApplicationReview).where(
            ApplicationReview.review_officer_id == user_id,
            ApplicationReview.status == ReviewStatus.COMPLETED,
            ApplicationReview.updated_at.between(year_start, year_end)
        )
    )

    # Completed by year
    completed_by_year_query = await db.execute(
        select(
            extract("year", ApplicationReview.updated_at).label("year"),
            func.count().label("count")
        ).where(
            ApplicationReview.review_officer_id == user_id,
            ApplicationReview.status == ReviewStatus.COMPLETED
        ).group_by("year").order_by("year")
    )
    completed_by_year = [
        {"year": int(row.year), "count": row.count}
        for row in completed_by_year_query
    ]

    # Average review time (in days)
    avg_duration_seconds = await db.scalar(
        select(
            func.avg(
                func.extract("epoch", ApplicationReview.updated_at - ApplicationReview.created_at)
            )
        ).where(
            ApplicationReview.review_officer_id == user_id,
            ApplicationReview.status == ReviewStatus.COMPLETED,
            ApplicationReview.created_at.isnot(None),
            ApplicationReview.updated_at.isnot(None)
        )
    )
    avg_duration_days = round(avg_duration_seconds / 86400, 1) if avg_duration_seconds else None

    # Steps completed
    steps_completed = await db.scalar(
        select(func.count()).select_from(ApplicationReviewStep).where(
            ApplicationReviewStep.reviewer_id == user_id,
            ApplicationReviewStep.completed.is_(True)
        )
    )

    # Exceptions raised
    exceptions_raised = await db.scalar(
        select(func.count()).select_from(ApplicationReviewStep).where(
            ApplicationReviewStep.reviewer_id == user_id,
            ApplicationReviewStep.flagged.is_(True)
        )
    )

    return {
        "total_reviews_assigned": total_assigned or 0,
        "reviews_completed": total_completed or 0,
        "reviews_pending": pending or 0,
        "completed_today": completed_today or 0,
        "completed_this_week": completed_this_week or 0,
        "completed_this_month": completed_this_month or 0,
        "completed_this_year": completed_this_year or 0,
        "completed_by_year": completed_by_year,
        "average_review_time_days": avg_duration_days,
        "steps_completed": steps_completed or 0,
        "exceptions_raised": exceptions_raised or 0
    }
