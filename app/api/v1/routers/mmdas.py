from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import aget_db
from app.models.user import MMDA
from app.schemas.mmda import MMDABase  # You’ll need this schema

router = APIRouter(
    prefix="/mmdas",
    tags=["mmdas"]
)

@router.get("/", response_model=List[MMDABase])
async def get_all_mmdas(db: AsyncSession = Depends(aget_db)):
    result = await db.execute(select(MMDA))
    mmdas = result.scalars().all()
    return mmdas
