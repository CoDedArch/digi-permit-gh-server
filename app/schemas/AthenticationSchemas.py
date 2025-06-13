from pydantic import BaseModel, validator
from app.utils.contact_utils import normalize_contact


class SendOtpRequest(BaseModel):
    contact: str
    channel: str

    @validator("channel")
    def validate_channel(cls, v):
        if v not in ("email", "sms"):
            raise ValueError("Channel must be 'email' or 'sms'")
        return v

    @validator("contact", pre=True)
    def normalize_contact_value(cls, v, values):
        channel = values.get("channel")
        if channel:
            return normalize_contact(v, channel)
        return v


class VerifyOtpRequest(BaseModel):
    contact: str
    otp: str

    @validator("contact", pre=True)
    def normalize_contact_value(cls, v):
        # Default to 'sms' for VerifyOtpRequest if no channel field
        from app.utils.contact_utils import normalize_contact
        return normalize_contact(v, "sms")
