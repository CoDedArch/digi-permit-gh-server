from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.AthenticationSchemas import SendOtpRequest, VerifyOtpRequest
from app.core.database import aget_db
from app.services.otpService import OtpService
from slowapi import Limiter
from slowapi.util import get_remote_address


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

otp_service = OtpService()
limiter = Limiter(key_func=get_remote_address)

@router.post("/send-otp", status_code=200)
@limiter.limit("3/minute")
async def send_otp(
    request: Request,
    payload: SendOtpRequest,
    db: AsyncSession = Depends(aget_db)
):
    try:
        await otp_service.send_otp(payload.contact, payload.channel, db)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"OTP sent via {payload.channel}"}
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send OTP")


@router.post("/verify-otp", status_code=200)
@limiter.limit("3/minute")
async def verify_otp(
    request: Request,
    payload: VerifyOtpRequest,
    db: AsyncSession = Depends(aget_db)
):
    is_valid = await otp_service.verify_otp(payload.contact, payload.otp, db)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )

    return {"message": "OTP verified successfully"}
