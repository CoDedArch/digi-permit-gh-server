from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional

from app.core.constants import InspectionOutcome, InspectionStatus, InspectionType

class InspectionRequest(BaseModel):
    application_id: int
    requested_date: date
    inspection_type: InspectionType
    notes: Optional[str] = None


class ApplicationOut(BaseModel):
    project_name: str

    class Config:
        from_attributes = True


class OfficerOut(BaseModel):
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


class InspectionOut(BaseModel):
    id: int
    status: str
    scheduled_date: Optional[datetime]
    application: ApplicationOut = None
    inspection_officer: Optional[OfficerOut] = None

    class Config:
        from_attributes = True






class OfficerDetailOut(BaseModel):
    id: int
    first_name: str
    last_name: str

    class Config:
        orm_mode = True

class MMDAOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class ApplicationDetailOut(BaseModel):
    id: int
    project_name: str
    location: Optional[str] = None

    class Config:
        orm_mode = True

# Main inspection schema
class InspectionDetailOut(BaseModel):
    id: int
    inspection_type: InspectionType
    status: InspectionStatus
    outcome: Optional[InspectionOutcome] = None
    scheduled_date: Optional[datetime]
    actual_date: Optional[datetime] = None
    notes: Optional[str] = None
    is_reinspection: Optional[bool] = None 

    application: Optional[ApplicationDetailOut] = None
    inspection_officer: Optional[OfficerDetailOut] = None
    mmda: Optional[MMDAOut] = None

    class Config:
        orm_mode = True
        use_enum_values = True