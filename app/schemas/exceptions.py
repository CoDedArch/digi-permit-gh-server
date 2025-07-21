# schemas/exceptions.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ApplicationExceptionOut(BaseModel):
    application_id: int
    applicant_name: str
    flag_reason: Optional[str] = None
    flagged_at: Optional[datetime] = None
    violations: Optional[str] = None
    inspection_status: str
    inspection_date: Optional[datetime] = None

    class Config:
        from_attributes = True
