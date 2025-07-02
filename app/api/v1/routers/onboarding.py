from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import aget_db
from app.core.security import decode_jwt_token
from app.models.user import User, UserDocument, ProfessionalInCharge
from app.core.constants import DocumentType, VerificationStage
from app.schemas.User import OnboardingData
from datetime import datetime

from app.utils.contact_utils import normalize_contact

router = APIRouter(
    prefix="/onboarding",
    tags=["onboarding"]
    )

@router.post("/user/onboarding/update-user")
async def complete_onboarding(
    data: OnboardingData,
    request: Request,
    db: AsyncSession = Depends(aget_db)
):
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = decode_jwt_token(token)
        user_id = int(payload.get("sub"))
        auth_method = payload.get("method")  # Pass this during login
        onboardingStatus = payload.get("onboarding")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not onboardingStatus:
        raise HTTPException(status_code=401, detail="you have already Onboarded") 

    # 🔁 Update based on method
    if auth_method == "email" and not user.phone:
        if not data.phone:
            raise HTTPException(status_code=400, detail="Phone number required")
        user.phone = normalize_contact(data.phone, "sms")

    elif auth_method == "phone" and not user.email:
        if not data.email:
            raise HTTPException(status_code=400, detail="Email required")
        user.email = normalize_contact(data.email, "email")


    # ✅ Update general info
    user.first_name = data.first_name
    user.last_name = data.last_name
    user.other_name = data.other_name
    user.address = data.address
    user.alt_phone = data.alt_phone
    user.gender = data.gender
    user.date_of_birth = data.date_of_birth
    user.applicant_type_code = data.applicant_type_code
    user.verification_stage = VerificationStage.DOCUMENT_PENDING  # ⬅️
    user.is_active = False

    # 🪪 Save Ghana Card Documents
    db.add_all([
        UserDocument(user_id=user.id, document_type=DocumentType.IDENTIFICATION.value, file_url=data.documents.front),
        UserDocument(user_id=user.id, document_type=DocumentType.IDENTIFICATION.value, file_url=data.documents.back)
    ])

    # 🧑‍💼 Professional info if needed
    if data.firm_name or data.license_number:
        prof = ProfessionalInCharge(
            full_name=f"{data.first_name} {data.last_name}",
            email=user.email,
            phone=user.phone,
            firm_name=data.firm_name,
            license_number=data.license_number,
        )
        db.add(prof)

    await db.commit()

    return {"message": "Onboarding complete", "user_id": user.id}
