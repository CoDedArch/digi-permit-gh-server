from typing_extensions import Literal
from pydantic import BaseModel, Field, validator
from datetime import date, datetime, time
from typing import List, Optional

from app.core.constants import InspectionOutcome, InspectionStatus, InspectionType, PermitType
from app.models.inspection import InspectionPhoto

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

class InspectionPhotoOut(BaseModel):
    id: int
    inspection_id: Optional[int] = None
    file_url: str = Field(alias="file_path") 
    caption: Optional[str]
    uploaded_at: datetime
    uploaded_by: OfficerDetailOut # Assuming you have a UserOut model

    class Config:
        from_attributes = True
        populate_by_name = True  # Allow both field name and alias

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
    photos: List[InspectionPhotoOut] = []
    mmda: Optional[MMDAOut] = None

    @validator('scheduled_time', always=True)
    def extract_time(cls, v, values):
        if 'scheduled_date' in values and values['scheduled_date']:
            return values['scheduled_date'].time()
        return None

    class Config:
        from_attributes = True
        use_enum_values = True




class InspectionPhotoIn(BaseModel):
    file_path: str
    caption: Optional[str] = None

    class Config:
        from_attributes = True
        # Allow both field names
        populate_by_name = True

class InspectionCompleteIn(BaseModel):
    status: InspectionStatus = InspectionStatus.COMPLETED  # Default value
    outcome: InspectionOutcome
    notes: Optional[str] = None
    violations_found: Optional[str] = None
    photos: Optional[List[InspectionPhotoIn]] = None
    actual_date: Optional[datetime] = None

    @validator('status')
    def validate_status(cls, v):
        if v != InspectionStatus.COMPLETED:
            raise ValueError("Status must be 'completed'")
        return v
    
class InspectorViolationOut(BaseModel):
    application_id: int
    application_number: str
    project_name: str
    inspection_date: datetime
    inspection_type: str
    violations: str
    photos: List[InspectionPhotoOut]
    status: str
    recommendations: Optional[str] = None

class PaginatedViolationsOut(BaseModel):
    data: List[InspectorViolationOut]
    total: int
    page: int
    per_page: int