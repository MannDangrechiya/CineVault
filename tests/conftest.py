# CineVault OS — Global Pytest Fixtures & Test Harness
# Automatically configures mock DB dependency overrides and seed fallback when offline.

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
