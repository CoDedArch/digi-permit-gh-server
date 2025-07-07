# app/api/v1/routers/applications.py
import json
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from uuid import uuid4
from app.core.constants import PaymentPurpose, PaymentStatus
from app.core.database import aget_db
from app.core.security import decode_jwt_token
from app.models.application import PermitApplication, ApplicationStatus
from app.models.document import ApplicationDocument
from app.models.payment import Payment
from app.schemas.permit_application import PermitApplicationCreate
from app.models.user import ProfessionalInCharge, User
from app.services.geojson_to_ewkt import geojson_to_ewkt

router = APIRouter(prefix="/applications", tags=["applications"])

@router.post("/submit-application")
async def create_application(
    data: PermitApplicationCreate,
    request: Request,
    db: AsyncSession = Depends(aget_db)
):
    print("request Received")
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_jwt_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    architect_id = None
    
    if data.architect and (data.architect.full_name or data.architect.license_number):
        new_professional = ProfessionalInCharge(
            full_name=data.architect.full_name,
            email=data.architect.email,
            phone=data.architect.phone,
            firm_name=data.architect.firm_name,
            license_number=data.architect.license_number,
            role=data.architect.role or "architect",
        )
        db.add(new_professional)
        await db.flush()  # Get the ID before commit
        architect_id = new_professional.id
    else:
        result = await db.execute(
            select(ProfessionalInCharge.id).where(
            ProfessionalInCharge.email == user.email
            )
        )
        existing_prof = result.scalars().first()
        if existing_prof:
            architect_id = existing_prof

    # Create new application
    application = PermitApplication(
        applicant_id=user_id,
        permit_type_id=data.permitTypeId,
        mmda_id=int(data.mmdaId),
        architect_id=architect_id,
        project_name=data.projectName,
        project_description=data.projectDescription,
        project_address=data.projectAddress,
        parcel_number=data.parcelNumber,
        zoning_district_id=int(data.zoningDistrictId) if data.zoningDistrictId else None,
        zoning_use_id=int(data.zoningUseId) if data.zoningUseId else None,
        estimated_cost=data.estimatedCost,
        construction_area=data.constructionArea,
        expected_start_date=data.expected_start_date,
        expected_end_date=data.expected_end_date,
        drainage_type_id=int(data.drainageTypeId) if data.drainageTypeId else None,
        previous_land_use_id = (
            data.previousLandUseId
            if data.previousLandUseId and data.previousLandUseId != "none"
            else None
        ),
        latitude=data.latitude,
        longitude=data.longitude,
        parcel_geometry=geojson_to_ewkt(data.parcelGeometry) if data.parcelGeometry else None,
        spatial_data=geojson_to_ewkt(data.zoningDistrictSpatial) if data.zoningDistrictSpatial else None,
        project_location=f"SRID=4326;POINT({data.longitude} {data.latitude})" if data.longitude and data.latitude else None,
        setbacks={
            "front": data.setbackFront,
            "rear": data.setbackRear,
            "left": data.setbackLeft,
            "right": data.setbackRight,
        },
        floor_areas={
            "maxHeight": data.maxHeight,
            "maxCoverage": data.maxCoverage,
            "minPlotSize": data.minPlotSize,
            "bufferZones": data.bufferZones,
            "density": data.density,
            "landscapeArea": data.landscapeArea,
            "occupantCapacity": data.occupantCapacity,
        },
        site_conditions=data.siteConditionIds,
        gis_metadata={entry["key"]: entry["value"] for entry in data.gisMetadata or []},
        fire_safety_plan=data.fireSafetyPlan,                # ✅ NEW
        waste_management_plan=data.wasteManagementPlan, 
        status=ApplicationStatus.SUBMITTED,
        application_number=f"APP-{uuid4().hex[:6].upper()}",
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)

    # 🔗 Link any successful unlinked payment
    result = await db.execute(
        select(Payment)
        .where(
            Payment.user_id == user_id,
            Payment.purpose == PaymentPurpose.PROCESSING_FEE,
            Payment.status == PaymentStatus.COMPLETED,
            Payment.application_id.is_(None)
        )
        .order_by(Payment.payment_date.desc())  # get the most recent one
        .limit(1)
    )
    payment = result.scalar_one_or_none()

    if payment:
        payment.application_id = application.id
        db.add(payment)
        await db.commit()


    # Store documents
    for doc_type_id, upload in data.documentUploads.items():
        document = ApplicationDocument(
            application_id=application.id,
            document_type_id=int(doc_type_id),
            file_path=upload.file_url,  # ✅ Match column name
            uploaded_by_id=user_id,     # ✅ Match correct foreign key
        )
        db.add(document)


    await db.commit()
    return {"id": application.id}