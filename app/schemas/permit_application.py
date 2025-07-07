# app/schemas/permit_application.py
from pydantic import BaseModel, Field, confloat, field_validator, model_validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone

from app.core.constants import ApplicationStatus, DocumentStatus

SHORT_FORM_TYPES = {
    "sign_permit",
    "subdivision",
    "temporary_structure",
    "fittings_installation",
    "hoarding",
    "sand_weaning",
}

class DocumentUpload(BaseModel):
    file_url: str
    doc_type_id: str

class ArchitectInfo(BaseModel):
    full_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    firm_name: Optional[str]
    license_number: Optional[str]
    role: Optional[str] = "architect"

class PermitApplicationCreate(BaseModel):
    permitTypeId: str
    architect: Optional[ArchitectInfo] = None
    mmdaId: str
    architectId: Optional[str]
    projectName: str
    projectDescription: Optional[str]
    projectAddress: str
    parcelNumber: Optional[str]
    zoningDistrictId: Optional[str] = None
    zoningUseId: Optional[str] = None
    estimatedCost: Optional[float]
    constructionArea: Optional[float]
    expected_start_date: Optional[Union[str, datetime]] = Field(alias="expectedStartDate")
    expected_end_date: Optional[Union[str, datetime]] = Field(alias="expectedEndDate")
    drainageTypeId: Optional[str] = None
    siteConditionIds: List[int] = []
    previousLandUseId: Optional[str] = None
    latitude: Optional[float]
    longitude: Optional[float]
    parcelGeometry: Optional[Dict[str, Any]] = None
    projectLocation: Optional[Dict[str, Any]]
    zoningDistrictSpatial: Optional[Dict[str, Any]] = None
    maxHeight: Optional[float]
    maxCoverage: Optional[float]
    minPlotSize: Optional[float]
    parkingSpaces: Optional[int]
    setbacks: Optional[str]
    bufferZones: Optional[str]
    density: Optional[str]
    landscapeArea: Optional[float]
    occupantCapacity: Optional[int]
    fireSafetyPlan: Optional[str] = None
    wasteManagementPlan: Optional[str] = None
    setbackFront: Optional[float]
    setbackRear: Optional[float]
    setbackLeft: Optional[float]
    setbackRight: Optional[float]
    gisMetadata: Optional[List[Dict[str, str]]]
    documentUploads: Dict[str, DocumentUpload]

    # def __init__(self, **data):
    #     print("📦 Full raw input to PermitApplicationCreate:", data)
    #     super().__init__(**data)


    @field_validator("expected_start_date", "expected_end_date", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        print("🕵️ Received datetime value:", v)

        if isinstance(v, str):
            try:
                # Replace 'Z' (Zulu time) with '+00:00' for ISO 8601 compliance
                v = datetime.fromisoformat(v.replace("Z", "+00:00"))
            except Exception as e:
                print("❌ Error parsing datetime:", e)
                raise ValueError("Invalid datetime format")

        if isinstance(v, datetime):
            if v.tzinfo is None:
                print("🕐 Making datetime timezone-aware (UTC)")
                return v.replace(tzinfo=timezone.utc)
            else:
                # Normalize to UTC if it has tzinfo
                return v.astimezone(timezone.utc)

        raise ValueError("Expected a string or datetime")

    @model_validator(mode="before")
    @classmethod
    def relax_fields_for_short_form_permits(cls, values):
        permit_type = values.get("permitTypeId")

        if permit_type in SHORT_FORM_TYPES:
            # Treat empty string or missing as None for optional short-form fields
            optional_fields = [
                "zoningDistrictId",
                "zoningUseId",
                "parcelGeometry",
                "zoningDistrictSpatial",
                "drainageTypeId",
                "fireSafetyPlan",
                "wasteManagementPlan",
                "previousLandUseId",
            ]

            for field in optional_fields:
                if field in values and (values[field] == "" or values[field] is None):
                    values[field] = None

        return values
    
    class Config:
        populate_by_name = True  # 🔥 KEY FIX FOR Pydantic v2
        arbitrary_types_allowed = True

class DocumentTypeOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
        from_attributes = True


class ApplicationDocumentOut(BaseModel):
    document_type: DocumentTypeOut
    file_path: str
    status: DocumentStatus

    class Config:
        orm_mode = True
        from_attributes = True


class MMDAOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
        from_attributes = True


class PermitTypeOut(BaseModel):
    id: str
    name: str

    class Config:
        orm_mode = True
        from_attributes = True


class ApplicationOut(BaseModel):
    id: int
    application_number: str
    project_name: str
    status: ApplicationStatus
    created_at: datetime
    permit_type: PermitTypeOut
    mmda: MMDAOut
    documents: List[ApplicationDocumentOut]

    class Config:
        orm_mode = True
        from_attributes = True


class ApplicationUpdate(BaseModel):
    project_name: Optional[str]
    project_description: Optional[str]
    expected_start_date: Optional[datetime]
    expected_end_date: Optional[datetime]
    parcel_number: Optional[str]
    project_address: Optional[str]
    parking_spaces: Optional[int]
    setbacks: Optional[Dict[str, float]]
    floor_areas: Optional[Dict[str, float]]
    site_conditions: Optional[Dict[str, str]]
    estimated_cost: Optional[float]
    construction_area: Optional[float]


# Nested models
class ZoningUseOut(BaseModel):
    use: str

    model_config = {
    "from_attributes": True
    }

class DrainageTypeOut(BaseModel):
    name: Optional[str] = None

    model_config = {
    "from_attributes": True
    }

class ZoningDistrictOut(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None

    model_config = {
    "from_attributes": True
    }

class PreviousLandUseOut(BaseModel):
    name: Optional[str] = None

    model_config = {
    "from_attributes": True
    }

class SiteConditionOut(BaseModel):
    name: str 

    model_config = {
    "from_attributes": True
    }

class ArchitectOut(BaseModel):
    full_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    firm_name: Optional[str]
    role: Optional[str]
    license_number: Optional[str]

    model_config = {
    "from_attributes": True
    }

class MMDAOut(BaseModel):
    id: int
    name: str

    model_config = {
    "from_attributes": True
    }

class ApplicantOut(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str]
    phone: Optional[str]


    model_config = {
    "from_attributes": True
    }

class PermitTypeOut(BaseModel):
    id: str
    name: str

    model_config = {
    "from_attributes": True
    }

# class DocumentOut(BaseModel):
#     name: Optional[str]
#     url: Optional[str]
#     permit_type: Optional[PermitTypeOut]

#     model_config = {
#     "from_attributes": True
#     }

class PaymentOut(BaseModel):
    amount: float
    status: str
    purpose: str
    payment_date: datetime
    due_date: Optional[datetime]
    transaction_reference: str

    model_config = {
    "from_attributes": True
    }


class Setbacks(BaseModel):
    left: Optional[float] = None
    right: Optional[float] = None
    front: Optional[float] = None
    rear: Optional[float] = None

class FloorAreas(BaseModel):
    density: Optional[float]
    bufferZones: Optional[float]

    @field_validator('density', 'bufferZones', mode="before")
    @classmethod
    def convert_empty_string_to_none(cls, v):
        if v == "":
            return None
        return v

class ApplicationDetailOut(BaseModel):
    id: int
    application_number: str
    status: str

    project_name: str
    project_description: Optional[str]
    parking_spaces: Optional[int]
    setbacks: Optional[Setbacks] = None
    floor_areas: Optional[FloorAreas] = None
    site_conditions: Optional[List[SiteConditionOut]] = None

    project_address: str
    parcel_number: Optional[str]

    estimated_cost: Optional[float]
    construction_area: Optional[float]
    expected_start_date: Optional[datetime]
    expected_end_date: Optional[datetime]
    fire_safety_plan: Optional[str] = None
    waste_management_plan: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]

    latitude: Optional[float]
    longitude: Optional[float]
    parcel_geometry: Optional[Any]  # You may serialize as GeoJSON
    spatial_data: Optional[Any]
    project_location: Optional[Any]
    gis_metadata: Optional[Dict[str, Any]]

    zoning_use: Optional[ZoningUseOut]
    drainage_type: Optional[DrainageTypeOut] = None
    zoning_district: Optional[ZoningDistrictOut]
    previous_land_use: Optional[PreviousLandUseOut]
    architect: Optional[ArchitectOut]
    mmda: MMDAOut
    applicant: Optional[ApplicantOut]
    permit_type: Optional[PermitTypeOut]
    documents: Optional[List[ApplicationDocumentOut]]
    payments: Optional[List[PaymentOut]]

    model_config = {
    "from_attributes": True
    }
