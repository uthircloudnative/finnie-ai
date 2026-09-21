"""
user.py — SQLAlchemy ORM model for User Accounts
=================================================
Stores user identity, hashed credentials, and preferences for multi-tenant isolation.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer
from src.database import Base


class User(Base):
    __tablename__ = "users"

    id              = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email           = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name       = Column(String, nullable=False)
    base_currency   = Column(String, default="USD")
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    token_version   = Column(Integer, default=1, nullable=False)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
