from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(
    prefix="/applications",
    tags=["applications"]
)

@router.get("/")
async def list_applications():
    return {"message": "List of applications"}

@router.post("/")
async def create_application(application_data: dict):
    return {"message": "Application created", "data": application_data}

@router.get("/{application_id}")
async def get_application(application_id: int):
    return {"message": f"Details of application {application_id}"}

@router.put("/{application_id}")
async def update_application(application_id: int, application_data: dict):
    return {"message": f"Application {application_id} updated", "data": application_data}

@router.delete("/{application_id}")
async def delete_application(application_id: int):
    return {"message": f"Application {application_id} deleted"}