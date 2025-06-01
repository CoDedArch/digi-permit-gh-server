from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List

router = APIRouter(
    prefix="/payments",
    tags=["payments"]
)

# Example payment model
class Payment(BaseModel):
    id: int
    amount: float
    status: str

# In-memory storage for demonstration
payments_db = []

@router.get("/", response_model=List[Payment])
def list_payments():
    return payments_db

@router.post("/", response_model=Payment, status_code=status.HTTP_201_CREATED)
def create_payment(payment: Payment):
    payments_db.append(payment)
    return payment

@router.get("/{payment_id}", response_model=Payment)
def get_payment(payment_id: int):
    for payment in payments_db:
        if payment.id == payment_id:
            return payment
    raise HTTPException(status_code=404, detail="Payment not found")