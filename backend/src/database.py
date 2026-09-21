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
_LOCAL_DB_PATH = os.path.join(BACKEND_DIR, "finnie.db")

# In cloud deployments (Azure/AWS/GCP), provide DATABASE_URL (e.g. PostgreSQL).
# If DATABASE_URL is not set, defaults to local or persistent SQLite via DB_PATH.
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    DB_PATH = os.environ.get("DB_PATH", _LOCAL_DB_PATH)
    DATABASE_URL = f"sqlite:///{DB_PATH}"

# SQLite requires check_same_thread=False; PostgreSQL/MySQL do not accept this argument
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


def get_db():
    """
    FastAPI dependency — yields a DB session per request, always closed after.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables defined via Base.metadata on first startup and apply schema migrations."""
    from src.models.user import User                      # noqa: F401
    from src.models.password_reset import PasswordResetAudit # noqa: F401
    from src.models.portfolio import Holding              # noqa: F401
    from src.models.market_metadata import MarketExchange # noqa: F401
    from src.models.market_cache import MarketCache       # noqa: F401
    from src.models.goal import FinancialGoal             # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Automatic schema migration for new columns on existing tables
    from sqlalchemy import inspect, text
    with engine.connect() as conn:
        inspector = inspect(engine)
        if "users" in inspector.get_table_names():
            columns = [col["name"] for col in inspector.get_columns("users")]
            if "token_version" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN token_version INTEGER DEFAULT 1 NOT NULL"))
                conn.commit()


