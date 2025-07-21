# routers/exceptions.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import aget_db
from app.models.review import ApplicationReviewStep
from app.models.inspection import Inspection
from app.schemas.exceptions import ApplicationExceptionOut

router = APIRouter(
    prefix="/exceptions",
    tags=["exceptions"]
)

@router.get("/reviewer/exceptions", response_model=list[ApplicationExceptionOut])
async def get_application_exceptions(db: AsyncSession = Depends(aget_db)):
    # Get all flagged application review steps
    flagged_stmt = (
        select(ApplicationReviewStep)
        .options(
            selectinload(ApplicationReviewStep.application),
            selectinload(ApplicationReviewStep.reviewer),
        )
        .where(ApplicationReviewStep.flagged == True)
    )
    flagged_steps_result = await db.execute(flagged_stmt)
    flagged_steps = flagged_steps_result.scalars().all()

    # Get all inspections with violations
    violations_stmt = (
        select(Inspection)
        .options(
            selectinload(Inspection.application),
            selectinload(Inspection.applicant),
        )
        .where(Inspection.violations_found.isnot(None))
    )
    violations_result = await db.execute(violations_stmt)
    inspections_with_violations = violations_result.scalars().all()

    # Use application_id to avoid duplicates
    seen_apps = set()
    exceptions = []

    for step in flagged_steps:
        app_id = step.application_id
        if app_id in seen_apps:
            continue
        seen_apps.add(app_id)

        # Find corresponding inspection, if any
        related_inspections = [
            i for i in inspections_with_violations if i.application_id == app_id
        ]
        inspection = related_inspections[0] if related_inspections else None

        exceptions.append(ApplicationExceptionOut(
            application_id=app_id,
            applicant_name=f"{step.application.applicant.first_name} {step.application.applicant.last_name}"
            if step.application.applicant else "Unknown",
            flag_reason=step.flag_reason,
            flagged_at=step.flagged_at,
            violations=inspection.violations_found if inspection else None,
            inspection_status=inspection.status.name if inspection else "Pending",
            inspection_date=inspection.actual_date if inspection else None
        ))

    # Add remaining violations not already in flagged list
    for inspection in inspections_with_violations:
        if inspection.application_id in seen_apps:
            continue
        seen_apps.add(inspection.application_id)

        exceptions.append(ApplicationExceptionOut(
            application_id=inspection.application_id,
            applicant_name=f"{inspection.applicant.first_name} {inspection.applicant.last_name}"
            if inspection.applicant else "Unknown",
            flag_reason=None,
            flagged_at=None,
            violations=inspection.violations_found,
            inspection_status=inspection.status.name,
            inspection_date=inspection.actual_date
        ))

    return exceptions
