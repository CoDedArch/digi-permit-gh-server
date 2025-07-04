# app/schemas/permit_application.py
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone

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

    