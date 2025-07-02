# app/api/routes/uploads.py

import traceback
from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import aget_db
from app.core.security import decode_jwt_token
from app.models.user import User
from app.services.s3_uploadService import upload_file_to_s3

router = APIRouter(prefix="/uploads", tags=["uploads"])

@router.post("/user-documents")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(aget_db),
):
    # 🔐 Extract token from cookie
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_jwt_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # 🔍 Get user from DB
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 📤 Upload to S3 with user-named folder
    try:
        url = upload_file_to_s3(
            file,
            folder="uploads/user_documents/ghanacards",
            username=user.full_name or user.email
        )
        return {"file_url": url}
    except Exception as e:
        print("UPLOAD ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/application-documents")
async def upload_application_document(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(aget_db)
):
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_jwt_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        url = upload_file_to_s3(
            file,
            folder="uploads/application_documents",
            username=user.full_name or user.email
        )
        return {"file_url": url}
    except Exception as e:
        print("UPLOAD ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
