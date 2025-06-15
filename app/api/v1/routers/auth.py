from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.AthenticationSchemas import SendOtpRequest, VerifyOtpRequest
from authlib.integrations.starlette_client import OAuth
from app.core.database import aget_db
from app.services.otpService import OtpService
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.services.otpService import OTPVerificationStatus
import os
from dotenv import load_dotenv

load_dotenv()


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

otp_service = OtpService()
limiter = Limiter(key_func=get_remote_address)

@router.post("/send-otp", status_code=200)
@limiter.limit("3/minute")
@router.post("/send-otp")
async def send_otp(
    request: Request,
    payload: SendOtpRequest,
    db: AsyncSession = Depends(aget_db)
):
    try:
        await otp_service.send_otp(payload.contact, payload.channel, db)
        return {"message": f"OTP sent via {payload.channel}"}

    except ValueError as ve:
        # Catch expected issues like locked user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Too many incorrect attempts. You have been temporarily locked out."
        )

    except Exception as e:
        # Log unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/verify-otp", status_code=200)
@limiter.limit("3/minute")
async def verify_otp(
    request: Request,
    payload: VerifyOtpRequest,
    db: AsyncSession = Depends(aget_db)
):
    print("Formatted Response from the user", payload.contact, payload.otp)

    verification_status = await otp_service.verify_otp(payload.contact, payload.otp, db)

    if verification_status == OTPVerificationStatus.SUCCESS:
        return {"message": "OTP verified successfully"}

    elif verification_status == OTPVerificationStatus.NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    elif verification_status == OTPVerificationStatus.CODE_EXPIRED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The verification code has expired. Please request a new one."
        )

    elif verification_status == OTPVerificationStatus.CODE_INVALID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code. Please try again."
        )

    elif verification_status == OTPVerificationStatus.MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Too many incorrect attempts. You have been temporarily locked out."
        )

    elif verification_status == OTPVerificationStatus.LOCKED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is temporarily locked. Please try again later."
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


# Google login endpoint
@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = request.url_for('google_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

# Google callback endpoint
@router.get("/google/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(aget_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = await oauth.google.parse_id_token(request, token)

        # You can access: user_info['email'], user_info['name'], user_info['sub'] (unique ID), etc.

        # TODO: Create/find user in your DB
        # user = await your_user_crud.get_or_create_user(user_info['email'], db)

        return JSONResponse({
            "message": "Google authentication successful",
            "user": {
                "name": user_info.get("name"),
                "email": user_info.get("email"),
                "sub": user_info.get("sub")
            }
        })

    except Exception as e:
        raise HTTPException(status_code=400, detail="Google login failed")