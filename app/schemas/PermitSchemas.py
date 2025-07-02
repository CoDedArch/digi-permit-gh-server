from decimal import Decimal
from pydantic import BaseModel
from typing import Optional, List

class DocumentTypeSchema(BaseModel):
    id: int
    name: str
    code: Optional[str]
    
    class Config:
        orm_mode = True

class DocumentRequirementSchema(BaseModel):
    is_mandatory: bool
    document_type: DocumentTypeSchema
    conditional_logic: Optional[dict] = None
    notes: Optional[str] = None
    phase: Optional[str] = None
    
    class Config:
        orm_mode = True


class DocumentTypeOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        orm_mode = True
      

class PermitDocumentRequirementOut(BaseModel):
    id: int
    is_mandatory: bool
    conditional_logic: Optional[dict] = None
    notes: Optional[str] = None
    phase: str
    document_type: DocumentTypeOut  # ✅ Nested relationship

    class Config:
        orm_mode = True

class PermitTypeWithRequirements(BaseModel):
    id: str
    name: str
    description: Optional[str]
    is_active: bool
    base_fee: Decimal
    standard_duration_days: int
    required_documents: List[PermitDocumentRequirementOut]
    
    class Config:
        orm_mode = True

class PermitTypeOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    base_fee: float
    standard_duration_days: int
    is_active: bool

    class Config:
        orm_mode = True

class ZoningDistrictOut(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    max_height: Optional[float]
    max_coverage: Optional[float]
    min_plot_size: Optional[float]
    color_code: Optional[str]
    density: Optional[str]
    parking_requirement: Optional[str]
    setbacks: Optional[str]
    special_notes: Optional[str]
    population_served: Optional[str]
    buffer_zones: Optional[str]
    class Config:
        orm_mode = True

class ZoningUseDocumentRequirementOut(BaseModel):
    id: int
    is_mandatory: bool
    phase: Optional[str] = None
    notes: Optional[str] = None
    document_type: DocumentTypeOut

    class Config:
        orm_mode = True


class ZoningPermittedUseOut(BaseModel):
    id: int
    zoning_district_id: int
    use: str
    requires_epa_approval: bool
    requires_heritage_review: bool
    requires_traffic_study: bool
    required_documents: List[ZoningUseDocumentRequirementOut] = []

    class Config:
        orm_mode = True

class DrainageTypeOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        orm_mode = True

class SiteConditionOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        orm_mode = True