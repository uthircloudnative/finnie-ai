"""
liability.py — SQLAlchemy ORM and Pydantic schemas for User Liabilities (SPEC-11)
==================================================================================
Stores individual user debt instruments (Credit Card, Mortgage, Auto Loan, Student Loan,
Personal Loan) with contractual APRs, monthly debt servicing payments (EMIs),
and amortization timelines per docs/DATA_MODEL.md.
"""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from src.database import Base


class Liability(Base):
    """
    SQLAlchemy ORM model for user liabilities.
    Multi-tenant isolation enforced via user_id foreign key.
    """
    __tablename__ = "liabilities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    
    # Debt classification: CREDIT_CARD, MORTGAGE, AUTO_LOAN, STUDENT_LOAN, PERSONAL
    liability_type = Column(String(32), nullable=False)
    lender_name = Column(String(100), default="Standard Lender", nullable=False)
    current_balance = Column(Float, nullable=False)
    interest_rate_apr = Column(Float, nullable=False)  # e.g. 24.0 for 24% APR
    monthly_payment = Column(Float, nullable=False)    # Minimum payment or EMI
    remaining_months = Column(Integer, nullable=False) # Repayment horizon in months
    country = Column(String(16), default="USA", nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return (
            f"<Liability id={self.id} user={self.user_id} type={self.liability_type} "
            f"balance={self.current_balance} apr={self.interest_rate_apr}% payment={self.monthly_payment}>"
        )


# ── Pydantic Request / Response Schemas ──

class LiabilityBase(BaseModel):
    liability_type: str = Field(..., description="CREDIT_CARD, MORTGAGE, AUTO_LOAN, STUDENT_LOAN, PERSONAL")
    lender_name: str = Field(default="Standard Lender", description="Name of creditor or institution")
    current_balance: float = Field(..., ge=0.0, description="Outstanding principal balance")
    interest_rate_apr: float = Field(..., ge=0.0, description="Annual Percentage Rate (APR %)")
    monthly_payment: float = Field(..., ge=0.0, description="Monthly payment or EMI")
    remaining_months: int = Field(..., ge=0, description="Months remaining to payoff")
    country: Optional[str] = Field(default="USA", description="Country jurisdiction")


class LiabilityCreate(LiabilityBase):
    pass


class LiabilityUpdate(BaseModel):
    liability_type: Optional[str] = None
    lender_name: Optional[str] = None
    current_balance: Optional[float] = None
    interest_rate_apr: Optional[float] = None
    monthly_payment: Optional[float] = None
    remaining_months: Optional[int] = None
    country: Optional[str] = None


class LiabilityResponse(LiabilityBase):
    id: int
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True
