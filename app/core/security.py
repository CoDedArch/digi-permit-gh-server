import hashlib
from typing import Optional
from datetime import datetime, timedelta
import jwt
from .config import settings


def hash_key(key: str) -> str:
    """Hash the key using SHA-256."""
    key = key or ""
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(api_key: Optional[str] = None) -> bool:
    """
    Verify the API key hashed is the same as the one in the settings.

    Args:
        - api_key (Optional[str]): The API key to verify.
        
    Returns:
        - bool: Whether the API key is valid.
    """
    if hash_key(api_key) == settings.HASHED_API_KEY:
        return True
    return False


def create_jwt_token(data: dict, expires_delta: timedelta = timedelta(hours=1)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()  # Add issued at time
    })
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    print("Created token:", token)  # Debug print
    return token

def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        print("Decoded payload:", payload)  # Debug print
        return payload
    except Exception as e:
        print(f"JWT Decode Error: {str(e)}")  # Detailed error logging
        raise