"""
cashflow.py — SQLAlchemy ORM and Pydantic schemas for User Cashflow Profiles (SPEC-11)
========================================================================================
Persists user's monthly income, fixed living expenses, and rolling discretionary
spending to compute sustainable investable cash flow per docs/DATA_MODEL.md.
"""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from src.database import Base


class UserCashflowProfile(Base):
    """
    SQLAlchemy ORM model for user cashflow profiles.
    Strict 1:1 multi-tenant linkage to User.
    """
    __tablename__ = "user_cashflow_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        String(64), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        unique=True, 
        index=True, 
        nullable=False
    )
    
    monthly_take_home = Column(Float, default=0.0, nullable=False)
    fixed_living_costs = Column(Float, default=0.0, nullable=False)
    monthly_discretionary_spend = Column(Float, default=0.0, nullable=False)
    country = Column(String(16), default="USA", nullable=False)
    
    updated_at = Column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return (
            f"<UserCashflowProfile user={self.user_id} income={self.monthly_take_home} "
            f"fixed={self.fixed_living_costs} spend={self.monthly_discretionary_spend} country={self.country}>"
        )


# ── Pydantic Request / Response Schemas ──

class CashflowProfileBase(BaseModel):
    monthly_take_home: float = Field(default=0.0, ge=0.0, description="Monthly after-tax take-home earnings")
    fixed_living_costs: float = Field(default=0.0, ge=0.0, description="Fixed living costs (rent, utilities, food)")
    monthly_discretionary_spend: float = Field(default=0.0, ge=0.0, description="Average credit card and lifestyle spend")
    country: Optional[str] = Field(default="USA", description="Country jurisdiction")


class CashflowProfileCreate(CashflowProfileBase):
    pass


class CashflowProfileUpdate(BaseModel):
    monthly_take_home: Optional[float] = None
    fixed_living_costs: Optional[float] = None
    monthly_discretionary_spend: Optional[float] = None
    country: Optional[str] = None


class CashflowProfileResponse(CashflowProfileBase):
    id: int
    user_id: str
    free_cashflow: Optional[float] = None
    updated_at: datetime

    class Config:
        from_attributes = True
