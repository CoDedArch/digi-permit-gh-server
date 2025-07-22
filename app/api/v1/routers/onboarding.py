from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import aget_db
from app.core.security import decode_jwt_token
from sqlalchemy.orm import joinedload
from app.models.user import Committee, CommitteeMember, Department, DepartmentStaff, User, UserDocument, ProfessionalInCharge, UserProfile
from app.core.constants import DocumentType, UserRole, VerificationStage
from app.schemas.User import OnboardingData, StaffOnboardingRequest
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


@router.post("/user/staff/onboarding")
async def onboard_staff(
    payload: StaffOnboardingRequest,
    request: Request,
    db: AsyncSession = Depends(aget_db),
):
    # --- Step 1: Extract token and get user ---
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        token_payload = decode_jwt_token(token)
        user_id = int(token_payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # --- Step 2: Validate and update role ---
    try:
        new_role = UserRole(payload.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role specified")

    user.role = new_role
    user.is_active = True

    # --- Step 3: Get or create user profile ---
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    profile.specialization = payload.specialization
    profile.work_email = payload.work_email
    profile.staff_number = payload.staff_number
    profile.designation = payload.designation

    # --- Step 4: Reassign Department and MMDA ---
    # Remove old DepartmentStaff entries from other MMDAs
    existing_staff = await db.execute(
        select(DepartmentStaff)
        .join(Department)
        .options(joinedload(DepartmentStaff.department))
        .filter(DepartmentStaff.user_id == user.id)
    )
    for staff_record in existing_staff.scalars():
        if staff_record.department.mmda_id != payload.mmda_id:
            await db.delete(staff_record)

    # Ensure department belongs to the provided MMDA
    department = await db.get(Department, payload.department_id)
    if not department or department.mmda_id != payload.mmda_id:
        raise HTTPException(status_code=400, detail="Department does not belong to the selected MMDA")

    # Create or update DepartmentStaff
    result = await db.execute(
        select(DepartmentStaff).where(
            DepartmentStaff.user_id == user.id,
            DepartmentStaff.department_id == payload.department_id
        )
    )
    dept_staff = result.scalar_one_or_none()

    if not dept_staff:
        dept_staff = DepartmentStaff(
            department_id=payload.department_id,
            user_id=user.id,
            position=payload.designation or "Officer"
        )
        db.add(dept_staff)
    else:
        dept_staff.position = payload.designation or dept_staff.position

    await db.flush()  # Ensure we have dept_staff.id for committee assignment

    # --- Step 5: Reassign Committees if needed ---
    # Remove committee memberships from other MMDAs
    existing_committees = await db.execute(
        select(CommitteeMember)
        .join(Committee)
        .options(joinedload(CommitteeMember.committee))
        .filter(CommitteeMember.staff_id == dept_staff.id)  # Changed to filter by staff_id
    )
    for committee_member in existing_committees.scalars():
        if committee_member.committee.mmda_id != payload.mmda_id:
            await db.delete(committee_member)

    # Ensure committee belongs to provided MMDA
    committee = await db.get(Committee, payload.committee_id)
    if not committee or committee.mmda_id != payload.mmda_id:
        raise HTTPException(status_code=400, detail="Committee does not belong to the selected MMDA")

    # Create or update CommitteeMember
    result = await db.execute(
        select(CommitteeMember).where(
            CommitteeMember.staff_id == dept_staff.id,  # Changed to use staff_id
            CommitteeMember.committee_id == payload.committee_id
        )
    )
    committee_member = result.scalar_one_or_none()

    if not committee_member:
        committee_member = CommitteeMember(
            committee_id=payload.committee_id,
            staff_id=dept_staff.id,  # Using staff_id instead of user_id
            role=payload.role.replace("_", " ").title()
        )
        db.add(committee_member)
    else:
        committee_member.role = payload.role.replace("_", " ").title()

    await db.commit()

    return {"message": "User onboarding completed successfully"}