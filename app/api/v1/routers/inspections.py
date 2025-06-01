from fastapi import APIRouter, HTTPException, status
from typing import List
from pydantic import BaseModel

router = APIRouter(
    prefix="/inspections",
    tags=["inspections"]
)

# Example Pydantic model for Inspection
class Inspection(BaseModel):
    id: int
    project_id: int
    inspector: str
    date: str
    status: str

# In-memory storage for demonstration
inspections_db = []

@router.get("/", response_model=List[Inspection])
def list_inspections():
    return inspections_db

@router.post("/", response_model=Inspection, status_code=status.HTTP_201_CREATED)
def create_inspection(inspection: Inspection):
    inspections_db.append(inspection)
    return inspection

@router.get("/{inspection_id}", response_model=Inspection)
def get_inspection(inspection_id: int):
    for inspection in inspections_db:
        if inspection.id == inspection_id:
            return inspection
    raise HTTPException(status_code=404, detail="Inspection not found")

@router.put("/{inspection_id}", response_model=Inspection)
def update_inspection(inspection_id: int, updated: Inspection):
    for idx, inspection in enumerate(inspections_db):
        if inspection.id == inspection_id:
            inspections_db[idx] = updated
            return updated
    raise HTTPException(status_code=404, detail="Inspection not found")

@router.delete("/{inspection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inspection(inspection_id: int):
    for idx, inspection in enumerate(inspections_db):
        if inspection.id == inspection_id:
            del inspections_db[idx]
            return
    raise HTTPException(status_code=404, detail="Inspection not found")