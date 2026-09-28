"""
goal.py — SQLAlchemy ORM model for user financial goals
======================================================
Stores persistent goal configurations (Target Amount, Year, Monthly Contributions),
LangGraph checkpoint thread linkages, and strategy outputs for the Autonomous
Financial GPS engine (SPEC-10 & docs/DATA_MODEL.md).
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, UniqueConstraint
from src.database import Base


class FinancialGoal(Base):
    """
    Stores a financial goal for a user.
    Enforces composite unique constraint on (user_id, goal_name).
    """
    __tablename__ = "financial_goals"
    __table_args__ = (
        UniqueConstraint("user_id", "goal_name", name="uq_user_goal_name"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)  # e.g. "user_1"
    
    goal_name = Column(String(100), default="Retirement", nullable=False)
    target_amount = Column(Float, nullable=False)         # e.g. 1000000.0
    target_year = Column(Integer, nullable=False)         # e.g. 2035
    monthly_contribution = Column(Float, default=0.0)     # e.g. 500.0
    
    # Jurisdiction context determining tax limits (USA, India, UK, etc.)
    country = Column(String(50), default="USA", nullable=False)
    
    # ── SPEC-10 In-Session Memory & HITL Lifecycle Enhancements ──
    # LangGraph checkpoint thread identifier (f"goal_{user_id}_{goal_id}")
    thread_id = Column(String(100), nullable=True, index=True)
    # Goal lifecycle state: "DRAFT", "LOCKED", "ACHIEVED"
    status = Column(String(20), default="LOCKED", nullable=False)
    # Monte Carlo probability of success percentage (0.0 - 100.0)
    confidence_score = Column(Float, nullable=True)
    # Full markdown report synthesized by the Goal Strategist and approved in HITL
    strategy_report = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<FinancialGoal user={self.user_id} name={self.goal_name} target={self.target_amount} status={self.status} thread={self.thread_id}>"
