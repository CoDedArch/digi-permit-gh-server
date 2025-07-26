import traceback
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from app.core.constants import InspectionStatus, UserRole
from app.core.database import aget_db
from app.core.security import decode_jwt_token
from app.models.inspection import Inspection
from app.models.user import Department, DepartmentStaff, User
from app.schemas.InspectionSchema import InspectorViolationOut


router = APIRouter(
    prefix="/violations",
    tags=["violations"]
)

@router.get("/inspector-violations", response_model=List[InspectorViolationOut])
async def get_inspector_violations(
    request: Request,
    db: AsyncSession = Depends(aget_db)
):
    try:
        print("Fetching inspector violations...")
        # Authentication
        token = request.cookies.get("auth_token")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        try:
            payload = decode_jwt_token(token)
            inspector_id = int(payload.get("sub"))
            print(f"Authenticated inspector ID: {inspector_id}")
        except ValueError as ve:
            print(f"ValueError converting inspector ID: {ve}")
            traceback.print_exc()
            raise HTTPException(status_code=401, detail="Invalid user ID in token")
        except Exception as e:
            print(f"Error decoding token: {e}")
            traceback.print_exc()
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        # Verify user is an inspector and get their department/MMDA
        try:
            # Check user role
            user = await db.get(User, inspector_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            if user.role != UserRole.INSPECTION_OFFICER:
                raise HTTPException(
                    status_code=403,
                    detail="Only inspection officers can access this data"
                )

            # Get department staff assignment
            staff_result = await db.execute(
                select(DepartmentStaff)
                .join(Department)
                .options(
                    joinedload(DepartmentStaff.department)
                    .joinedload(Department.mmda)
                )
                .filter(DepartmentStaff.user_id == inspector_id)
            )
            staff = staff_result.scalars().first()

            if not staff or not staff.department or not staff.department.mmda:
                raise HTTPException(
                    status_code=403,
                    detail="Inspector is not assigned to a department with MMDA"
                )

            mmda_id = staff.department.mmda.id
            print(f"Inspector belongs to MMDA: {mmda_id}")

        except Exception as e:
            print(f"Error verifying user department: {e}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail="Error verifying permissions")

        # Query for completed inspections with violations for the inspector's MMDA
        try:
            stmt = (
                select(Inspection)
                .options(
                    selectinload(Inspection.application),
                    selectinload(Inspection.photos),
                    selectinload(Inspection.inspection_officer)
                )
                .where(
                    Inspection.mmda_id == mmda_id,
                    Inspection.status == InspectionStatus.COMPLETED,
                    Inspection.violations_found != "",
                    Inspection.violations_found.isnot(None),
                    Inspection.inspection_officer_id == inspector_id
                )
                .order_by(Inspection.actual_date.desc())
            )

            inspections = (await db.execute(stmt)).scalars().all()
            print(f"Found {len(inspections)} violations for inspector {inspector_id}")

            # Build response
            violations = []
            for inspection in inspections:
                try:
                    violations.append(InspectorViolationOut(
                        application_id=inspection.application.id,
                        application_number=inspection.application.application_number,
                        project_name=inspection.application.project_name,
                        inspection_date=inspection.actual_date,
                        inspection_type=inspection.inspection_type.value,  # Convert enum to string
                        violations=inspection.violations_found,
                        photos=inspection.photos,
                        status=inspection.status.value,  # Convert enum to string
                        recommendations=inspection.recommendations
                    ))
                except Exception as e:
                    print(f"Error processing inspection {inspection.id}: {e}")
                    traceback.print_exc()
                    continue
            
            print("Violations", violations)
            return violations or []  # Return empty array if no violations

        except Exception as e:
            print(f"Database query error: {e}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail="Error fetching violations")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in get_inspector_violations: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")