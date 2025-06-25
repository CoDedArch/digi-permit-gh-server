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

class PermitTypeWithRequirements(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    requires_epa_approval: bool
    requires_heritage_review: bool
    required_documents: List[DocumentRequirementSchema] = []
    
    class Config:
        orm_mode = True