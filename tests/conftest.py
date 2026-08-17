import sys
from pathlib import Path

# Ensure project root is on sys.path for pytest
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from services.api.main import app
from services.api.database import get_db

async def override_get_db_fallback():
    """Yields None to trigger in-memory seed catalog & repository fallbacks during local tests."""
    yield None

@pytest.fixture(autouse=True)
def configure_test_environment():
    """Applies global dependency overrides before each test run."""
    app.dependency_overrides[get_db] = override_get_db_fallback
    yield
    app.dependency_overrides.pop(get_db, None)
