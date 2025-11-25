import os
import shutil
import sys
import tempfile
from pathlib import Path
import pytest
from dotenv import load_dotenv


@pytest.fixture(scope="session")
def media_tmpdir():
    tmpdir = tempfile.mkdtemp(prefix="media_photos_")
    os.environ["MEDIA_ROOT"] = tmpdir
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture(scope="session")
def app_instance(media_tmpdir):  # ensures MEDIA_ROOT and .env are set before import
    # Load .env from project root
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)

    # DB configuration comes from environment (docker-compose or local)
    from api.app.main import app
    return app


@pytest.fixture()
def client(app_instance):
    from fastapi.testclient import TestClient
    with TestClient(app_instance) as c:
        yield c


