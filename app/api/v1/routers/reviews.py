from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from pydantic import BaseModel

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"]
)

# Example Pydantic model for a review
class Review(BaseModel):
    id: int
    user_id: int
    permit_id: int
    rating: int
    comment: str

# In-memory storage for demonstration
fake_reviews_db = []

@router.get("/", response_model=List[Review])
def list_reviews():
    return fake_reviews_db

@router.post("/", response_model=Review, status_code=status.HTTP_201_CREATED)
def create_review(review: Review):
    fake_reviews_db.append(review)
    return review

@router.get("/{review_id}", response_model=Review)
def get_review(review_id: int):
    for review in fake_reviews_db:
        if review.id == review_id:
            return review
    raise HTTPException(status_code=404, detail="Review not found")

@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: int):
    for i, review in enumerate(fake_reviews_db):
        if review.id == review_id:
            del fake_reviews_db[i]
            return
    raise HTTPException(status_code=404, detail="Review not found")