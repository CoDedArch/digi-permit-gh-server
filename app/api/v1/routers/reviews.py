import traceback
from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import List
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import aget_db
from app.core.security import decode_jwt_token
from app.models.application import PermitApplication
from app.models.review import ApplicationReviewStep

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"]
)

# Example Pydantic model for a review
class Review(BaseModel):
    id: int
    user_id: int
    permit_id: int
    rating: int
    comment: str

# In-memory storage for demonstration
fake_reviews_db = []

@router.get("/", response_model=List[Review])
def list_reviews():
    return fake_reviews_db

@router.post("/", response_model=Review, status_code=status.HTTP_201_CREATED)
def create_review(review: Review):
    fake_reviews_db.append(review)
    return review

@router.get("/{review_id}", response_model=Review)
def get_review(review_id: int):
    for review in fake_reviews_db:
        if review.id == review_id:
            return review
    raise HTTPException(status_code=404, detail="Review not found")

@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: int):
    for i, review in enumerate(fake_reviews_db):
        if review.id == review_id:
            del fake_reviews_db[i]
            return
    raise HTTPException(status_code=404, detail="Review not found")

@router.get("/review-progress/{application_id}", response_model=dict)
async def get_review_progress(
    application_id: int,
    request: Request,
    db: AsyncSession = Depends(aget_db),
):
    """
    Returns the next review step for the current user on a specific application.
    """
    # Authentication
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_jwt_token(token)
        reviewer_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    try:
        # Get all steps for this application and reviewer
        stmt = (
            select(ApplicationReviewStep)
            .where(
                ApplicationReviewStep.application_id == application_id,
                ApplicationReviewStep.reviewer_id == reviewer_id,
            )
            .order_by(ApplicationReviewStep.id)
        )
        result = await db.execute(stmt)
        review_steps = result.scalars().all()

        # Define the expected step order
        STEP_ORDER = [
            "Overview",
            "Property Details",
            "Zoning Compliance",
            "Technical Review",
            "Timeline",
            "Documents",
            "Inspection Results",
            "Decision"
        ]

        # Find the first incomplete step
        next_step = None
        for step_name in STEP_ORDER:
            step = next((s for s in review_steps if s.step_name == step_name), None)
            if not step or not step.completed:
                next_step = step_name
                break

        # If all steps are completed, return the last step
        if not next_step and review_steps:
            next_step = STEP_ORDER[-1]

        # Get current application status
        app_result = await db.execute(
            select(PermitApplication.status)
            .where(PermitApplication.id == application_id)
        )
        app_status = app_result.scalar_one_or_none()

        return {
            "next_step": next_step,
            "current_status": app_status.value if app_status else None,
            "completed_steps": [s.step_name for s in review_steps if s.completed],
            "flagged_steps": [s.step_name for s in review_steps if s.flagged],
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching review progress: {str(e)}"
        )