from pydantic import BaseModel
from typing import Optional

class MMDABase(BaseModel):
    id: int
    name: str
    type: str
    region: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    jurisdiction_boundaries: Optional[dict] = None  # Add this

    class Config:
        orm_mode = True
