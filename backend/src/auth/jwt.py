"""
jwt.py — JWT Generation, Password Hashing & FastAPI Security Dependency
========================================================================
Stateless authentication service using HMAC-SHA256 JWT tokens.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.user import User

# System Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "finnie_ai_super_secret_jwt_key_2026_change_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    """Hashes a plain-text password using Bcrypt."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a Bcrypt hash."""
    pwd_bytes = plain_password.encode("utf-8")[:72]
    hash_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(pwd_bytes, hash_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generates a stateless JWT access token containing claims."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decodes a JWT access token and returns claims, or None if invalid/expired."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None



def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI Security Dependency:
    Validates incoming Bearer JWT token, decodes user ID, and fetches User from DB.
    Falls back to demo user_1 if no token provided (for backwards compatibility).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        # Fallback for unauthenticated dev requests: return/create demo user
        demo_user = db.query(User).filter(User.id == "user_1").first()
        if not demo_user:
            demo_user = User(
                id="user_1",
                email="demo@finnie.ai",
                hashed_password=hash_password("demopassword"),
                full_name="Demo Investor"
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
        return demo_user

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user
