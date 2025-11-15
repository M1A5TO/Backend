import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

from .models import Base

# Load .env file from project root
project_root = Path(__file__).resolve().parents[2]
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Build DATABASE_URL from existing env vars used elsewhere
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = int(os.getenv("POSTGRES_PORT", 5432))
PG_USER = os.getenv("POSTGRES_USER", "user")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
PG_DB = os.getenv("POSTGRES_DB", "db")

# Auto-detect: if POSTGRES_HOST is "postgres" (Docker service name) but we're not in Docker,
# try localhost instead. This allows the same .env to work in both environments.
if PG_HOST == "postgres" and not os.path.exists("/.dockerenv"):
    import socket
    try:
        # Try to resolve "postgres" hostname - if it fails, we're not in Docker network
        socket.gethostbyname("postgres")
    except (socket.gaierror, OSError):
        # Not in Docker network, use localhost
        PG_HOST = "localhost"

DATABASE_URL = (
    f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def ensure_database():
    """Ensure database is migrated; if Alembic isn't set up, create tables directly."""
    # Try Alembic upgrade if migrations folder exists
    migrations_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "migrations")
    try:
        if os.path.isdir(migrations_path):
            from alembic import command
            from alembic.config import Config

            cfg = Config()
            cfg.set_main_option("script_location", migrations_path)
            cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
            command.upgrade(cfg, "head")
            return
    except Exception:
        # Fall back to create_all below
        pass

    # Fallback: create all tables if they don't exist
    try:
        Base.metadata.create_all(bind=engine)
    except OperationalError:
        # Bubble up for visibility if connection failed
        raise


def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
