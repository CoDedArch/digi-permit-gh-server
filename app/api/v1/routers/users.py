from fastapi import APIRouter, HTTPException, status
from typing import List
from pydantic import BaseModel

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

# Example user model (replace with your actual model)

class User(BaseModel):
    id: int
    username: str
    email: str

# Dummy database
fake_users_db = [
    {"id": 1, "username": "alice", "email": "alice@example.com"},
    {"id": 2, "username": "bob", "email": "bob@example.com"},
]

@router.get("/", response_model=List[User])
def list_users():
    return fake_users_db

@router.get("/{user_id}", response_model=User)
def get_user(user_id: int):
    user = next((u for u in fake_users_db if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(user: User):
    if any(u["id"] == user.id for u in fake_users_db):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID already exists")
    fake_users_db.append(user.dict())
    return user