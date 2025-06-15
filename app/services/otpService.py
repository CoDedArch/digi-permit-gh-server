from datetime import datetime, timedelta
from fastapi.exceptions import HTTPException
import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.user import UnverifiedUser
from app.services.sendEmailOtp import send_email_otp
from app.services.sendSmsOtp import send_sms_otp
from enum import Enum

MAX_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 15
OTP_EXPIRY_MINUTES = 5

class OTPVerificationStatus(str, Enum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    CODE_EXPIRED = "code_expired"
    CODE_INVALID = "code_invalid"
    MAX_ATTEMPTS = "max_attempts"
    LOCKED = "locked"


class OtpService:
    async def generate_otp(self, email_or_phone: str, db: AsyncSession) -> str:
        otp = str(secrets.randbelow(900000) + 100000)
        expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)

        try:
            result = await db.execute(
                select(UnverifiedUser).where(
                    (UnverifiedUser.email == email_or_phone) |
                    (UnverifiedUser.phone == email_or_phone)
                )
            )
            user = result.scalar_one_or_none()
        except Exception as e:
            print(f"Query failed: {type(e).__name__}: {e}")
            raise

        now = datetime.utcnow()

        if user:
            if user.is_locked and user.lock_expires and user.lock_expires > now:
                raise ValueError("User is temporarily locked due to too many failed attempts. Please try again later.")

            # Reset OTP and unlock user if lock expired
            if user.lock_expires and user.lock_expires <= now:
                user.is_locked = False
                user.verification_attempts = 0
                user.lock_expires = None

            user.otp_secret = otp
            user.otp_expires = expires_at
            user.verification_attempts = 0
        else:
            user = UnverifiedUser(
                email=email_or_phone if "@" in email_or_phone else None,
                phone=None if "@" in email_or_phone else email_or_phone,
                otp_secret=otp,
                otp_expires=expires_at,
                verification_attempts=0,
                is_locked=False,
                lock_expires=None,
                verification_channel="email" if "@" in email_or_phone else "sms"
            )
            db.add(user)

        await db.commit()
        return otp

    
    async def send_otp (self, contact: str,  channel:str, db: AsyncSession ):
        if channel not in ["email", "sms"]:
            raise ValueError("Invalid channel")
        # generate the otp
        try:
            otp = await self.generate_otp(contact, db)
        except ValueError as e:
            raise ValueError("User is temporarily locked due to too many failed attempts. Please try again later.")
        
        if channel == "email":
            await send_email_otp(contact, otp)
        else:
            await send_sms_otp(contact, otp)

    async def verify_otp(self, email_or_phone: str, input_code: str, db: AsyncSession) -> OTPVerificationStatus:
        result = await db.execute(
            select(UnverifiedUser).where(
                (UnverifiedUser.email == email_or_phone) |
                (UnverifiedUser.phone == email_or_phone)
            )
        )
        user = result.scalar_one_or_none()

        now = datetime.utcnow()

        if not user:
            return OTPVerificationStatus.NOT_FOUND

        if user.is_locked and user.lock_expires and user.lock_expires > now:
            return OTPVerificationStatus.LOCKED

        if user.otp_expires < now:
            return OTPVerificationStatus.CODE_EXPIRED

        if user.otp_secret != input_code:
            user.verification_attempts += 1
            if user.verification_attempts >= MAX_ATTEMPTS:
                user.is_locked = True
                user.lock_expires = now + timedelta(minutes=LOCK_DURATION_MINUTES)
                await db.commit()
                return OTPVerificationStatus.MAX_ATTEMPTS

            await db.commit()
            return OTPVerificationStatus.CODE_INVALID

        # OTP is correct
        await db.delete(user)
        await db.commit()
        return OTPVerificationStatus.SUCCESS