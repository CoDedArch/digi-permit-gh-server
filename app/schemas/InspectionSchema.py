from pydantic import BaseModel, Field, validator
from datetime import date, datetime, time
from typing import Optional

from app.core.constants import InspectionOutcome, InspectionStatus, InspectionType, PermitType

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




class PermitTypeOut(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


class ApplicationDetailOut(BaseModel):
    id: int
    application_number: str
    project_name: str
    # project_location: Optional[str] = None
    project_description: Optional[str] = None
    permit_type: Optional[PermitTypeOut] = None
    project_address: Optional[str] = None  # For project address

    class Config:
        from_attributes = True

class OfficerDetailOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    phone: Optional[str] = None

    class Config:
        from_attributes = True

class ApplicantDetailOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    phone: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    class Config:
        from_attributes = True


class MMDAOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class InspectionDetailOut(BaseModel):
    id: int
    inspection_type: InspectionType
    status: InspectionStatus
    outcome: Optional[InspectionOutcome] = None
    scheduled_date: Optional[datetime] = None
    scheduled_time: Optional[time] = None  # Extracted from scheduled_date
    actual_date: Optional[datetime] = None
    notes: Optional[str] = None
    is_reinspection: Optional[bool] = None 
    special_instructions: Optional[str] = None
    findings: Optional[str] = None
    recommendations: Optional[str] = None
    violations_found: Optional[str] = None

    application: Optional[ApplicationDetailOut] = None
    inspection_officer: Optional[OfficerDetailOut] = None
    applicant: Optional[ApplicantDetailOut] = None
    mmda: Optional[MMDAOut] = None

    @validator('scheduled_time', always=True)
    def extract_time(cls, v, values):
        if 'scheduled_date' in values and values['scheduled_date']:
            return values['scheduled_date'].time()
        return None

    class Config:
        from_attributes = True
        use_enum_values = True