from pydantic import BaseModel, EmailStr
from typing import Any, List, Optional
from datetime import datetime

from app.core.constants import ApplicationStatus
from app.schemas.permit_application import ApplicationDetailOut



class ReviewOut(BaseModel):
    id: int
    review_officer_id: int
    status: str
    comments: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class InspectionOut(BaseModel):
    id: int
    inspector_id: Optional[int] = None
    date: Optional[datetime] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class ReviewerPermitApplicationOut(ApplicationDetailOut):
    reviews: Optional[List[ReviewOut]] = None
    inspections: Optional[List[InspectionOut]] = None
    model_config = {"from_attributes": True}


class UpdateReviewStatusRequest(BaseModel):
    newStatus: ApplicationStatus
    comments: str

class FlagStepRequest(BaseModel):
    reason: str