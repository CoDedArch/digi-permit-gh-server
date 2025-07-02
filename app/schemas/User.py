from datetime import date
from typing import Optional
from pydantic import BaseModel

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