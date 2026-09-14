"""
goal.py — SQLAlchemy ORM model for user financial goals
======================================================
Stores persistent goal configurations (Target Amount, Year, Monthly Contributions)
for the Goal Strategist Monte Carlo engine.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime
from src.database import Base


class FinancialGoal(Base):
    """
    Stores a single financial goal for a user.
    Finnie currently supports one active 'Primary Goal' per user for the Strategist dashboard.
    """
    __tablename__ = "financial_goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)  # e.g. "user_1"
    
    goal_name = Column(String, default="Retirement")      # e.g. "Dream Home"
    target_amount = Column(Float, nullable=False)         # e.g. 1000000.0
    target_year = Column(Integer, nullable=False)         # e.g. 2035
    monthly_contribution = Column(Float, default=0.0)     # e.g. 500.0
    
    # Used for RAG-based tax/regulatory metadata filtering
    country = Column(String, default="US")                # e.g. "US", "IN"
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<FinancialGoal user={self.user_id} name={self.goal_name} target={self.target_amount} year={self.target_year}>"
