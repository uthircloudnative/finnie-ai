"""
password_reset.py — SQLAlchemy ORM model for Password Reset & Security Audits
=============================================================================
Stores OTP verification codes, attempt telemetry, and forensic audit records.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from src.database import Base


class PasswordResetAudit(Base):
    __tablename__ = "password_reset_audits"

    id                 = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id            = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Security & Verification ──────────────────────────────────────────
    code_hash          = Column(String, nullable=False)
    status             = Column(String, default="PENDING", nullable=False)  # PENDING, COMPLETED, EXPIRED, FAILED
    attempts           = Column(Integer, default=0, nullable=False)

    # ── Precise UTC Timestamps ───────────────────────────────────────────
    requested_at       = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at         = Column(DateTime(timezone=True), nullable=False)
    completed_at       = Column(DateTime(timezone=True), nullable=True)

    # ── Forensic Telemetry (Origin vs Completion) ────────────────────────
    request_ip         = Column(String, nullable=True)
    request_location   = Column(String, nullable=True)
    completed_ip       = Column(String, nullable=True)
    completed_location = Column(String, nullable=True)
    user_agent         = Column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<PasswordResetAudit id={self.id} user_id={self.user_id} status={self.status}>"
