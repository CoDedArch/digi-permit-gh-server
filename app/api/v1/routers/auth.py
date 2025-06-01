from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    # Dummy authentication logic, replace with real user validation
    if form_data.username == "admin" and form_data.password == "password":
        return {"access_token": "fake-jwt-token", "token_type": "bearer"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

@router.post("/logout")
async def logout() -> Any:
    # Implement logout logic if needed (e.g., token blacklist)
    return {"msg": "Successfully logged out"}