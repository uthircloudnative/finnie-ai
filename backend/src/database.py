"""
database.py — SQLite/SQLAlchemy session management
====================================================
Currently uses SQLite for zero-setup local development.
To switch to PostgreSQL for production, update DATABASE_URL only:

    DATABASE_URL = "postgresql+psycopg2://user:pass@host/dbname"

All other code (models, CRUD) stays identical thanks to SQLAlchemy's ORM.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Resolve path relative to backend root so the DB file is always predictable
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BACKEND_DIR, "finnie.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite + FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


def get_db():
    """
    FastAPI dependency — yields a DB session per request, always closed after.

    Usage in route:
        from src.database import get_db
        from sqlalchemy.orm import Session
        from fastapi import Depends

        @app.get("/something")
        def route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables defined via Base.metadata on first startup."""
    from src.models.portfolio import Holding  # noqa: F401 — registers the model
    Base.metadata.create_all(bind=engine)
