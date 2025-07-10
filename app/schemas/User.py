from datetime import date, datetime
from typing import Annotated, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints, constr, validator

class ApplicantTypeOut(BaseModel):
    id: int
    code: str
    name: str
    description: str | None = None

    class Config:
        orm_mode = True
class GhanaCardDocument(BaseModel):
    front: str  # URL to the front image
    back: str

class OnboardingData(BaseModel):
    email: str
    phone: str
    first_name: str
    last_name: str
    other_name: Optional[str] = None
    date_of_birth: date
    gender: str
    address: str
    applicant_type_code: Optional[str] = None
    alt_phone: Optional[str] = None
    firm_name: Optional[str] = None
    license_number: Optional[str] = None
    documents: GhanaCardDocument

class UserProfileOut(BaseModel):
    ghana_card_number: Optional[str] = None
    digital_address: Optional[str] = None
    specialization: Optional[str] = None
    work_email: Optional[str] = None
    staff_number: Optional[str] = None
    designation: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserOut(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    other_name: Optional[str] = None
    phone: str
    alt_phone: Optional[str] = None
    is_active: bool
    role: str
    verification_stage: str
    date_of_birth: Optional[datetime] = None
    gender: Optional[str]
    address: Optional[str] = None
    applicant_type_code: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class UserDocumentOut(BaseModel):
    id: int
    document_type: str
    file_url: str

    model_config = ConfigDict(from_attributes=True)


class CurrentUserResponse(BaseModel):
    authenticated: bool
    user: UserOut
    profile: Optional[UserProfileOut]
    documents: List[UserDocumentOut] = []


class GhanaCardInput(BaseModel):
    ghana_card_number: Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=20)]


class StaffOnboardingRequest(BaseModel):
    mmda_id: int
    department_id: int
    committee_id: int
    role: str
    specialization: Optional[str]
    work_email: Optional[EmailStr] = None
    staff_number: Optional[str]
    designation: Optional[str]

    @validator("work_email", pre=True)
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

class DepartmentBase(BaseModel):
    id: int
    name: str
    code: str

class CommitteeBase(BaseModel):
    id: int
    name: str
