from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from enum import Enum

from app.core.constants import PaymentPurpose


class PaymentMethod(str, Enum):
    MOMO = "momo"
    CARD = "card"
    BANK = "bank"


# class PaymentPurpose(str, Enum):
#     APPLICATION_SUBMISSION = "application_submission"
#     PERMIT_ISSUANCE = "permit_issuance"
#     INSPECTION_FEE = "inspection_fee"
#     OTHER = "other"


class PaymentRequest(BaseModel):
    amount: float = Field(..., gt=0)
    callback_url: HttpUrl

class PaymentInitRequest(BaseModel):
    amount: float
    email: str
    callback_url: str
    purpose: PaymentPurpose  # ✅ this must match the Enum
    notes: Optional[str] = None
    user_id: int
    reference: str

class PaymentInitResponse(BaseModel):
    authorization_url: str
    reference: str
    access_code: Optional[str] = None
    status: str = "success"
