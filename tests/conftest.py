import os
import shutil
import sys
import tempfile
from pathlib import Path
import pytest
from dotenv import load_dotenv
from sqlalchemy import text


@pytest.fixture(scope="session")
def media_tmpdir():
    tmpdir = tempfile.mkdtemp(prefix="media_photos_")
    os.environ["MEDIA_ROOT"] = tmpdir
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture(scope="session")
def app_instance(media_tmpdir):  # ensures MEDIA_ROOT and .env are set before import
    # Force POSTGRES_HOST to localhost for tests
    os.environ["POSTGRES_HOST"] = "localhost"
    
    # Load .env from project root
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    
    # Override POSTGRES_HOST again after loading .env to ensure it's always localhost
    os.environ["POSTGRES_HOST"] = "localhost"

    # DB configuration comes from environment (docker-compose or local)
    from api.app.main import app
    return app


@pytest.fixture(autouse=True)
def clear_database(app_instance):
    """Automatically clear database before each test"""
    from api.app.db import SessionLocal
    
    db = SessionLocal()
    try:
        # Ensure PostGIS extension is enabled
        db.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        db.commit()
        
        # Ensure SRID 4326 exists in spatial_ref_sys (PostGIS should have it by default, but ensure it)
        # Always try to insert SRID 4326 - use DO NOTHING to avoid errors if it already exists
        # Note: spatial_ref_sys may not have a unique constraint on srid, so we check first
        result = db.execute(text("SELECT COUNT(*) FROM spatial_ref_sys WHERE srid = 4326;"))
        count = result.scalar()
        if count == 0:
            # Insert SRID 4326 (WGS 84) if it doesn't exist
            # Escape single quotes in srtext properly
            db.execute(text("""
                INSERT INTO spatial_ref_sys (srid, auth_name, auth_srid, proj4text, srtext)
                VALUES (4326, 'EPSG', 4326, 
                    '+proj=longlat +datum=WGS84 +no_defs',
                    'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'
                );
            """))
            db.commit()
        
        # Disable foreign key checks temporarily
        db.execute(text("SET session_replication_role = 'replica';"))
        
        # Get all table names (exclude system tables like spatial_ref_sys)
        result = db.execute(text("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
            AND tablename != 'spatial_ref_sys'
        """))
        tables = [row[0] for row in result]
        
        # Truncate all tables
        for table in tables:
            db.execute(text(f'TRUNCATE TABLE "{table}" CASCADE;'))
        
        # Re-enable foreign key checks
        db.execute(text("SET session_replication_role = 'origin';"))
        db.commit()
    finally:
        db.close()
    yield
    # Cleanup after test (optional - truncate again if needed)
    db = SessionLocal()
    try:
        db.execute(text("SET session_replication_role = 'replica';"))
        result = db.execute(text("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
            AND tablename != 'spatial_ref_sys'
        """))
        tables = [row[0] for row in result]
        for table in tables:
            db.execute(text(f'TRUNCATE TABLE "{table}" CASCADE;'))
        db.execute(text("SET session_replication_role = 'origin';"))
        db.commit()
    finally:
        db.close()


@pytest.fixture()
def client(app_instance):
    from fastapi.testclient import TestClient
    with TestClient(app_instance) as c:
        yield c


