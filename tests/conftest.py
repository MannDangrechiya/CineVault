import os
import sys
from pathlib import Path

# Ensure project root is on sys.path for pytest
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Force the Mock AI provider for the whole test session, before
# services.api.config's module-level `config = APIConfig()` singleton is
# ever constructed (that happens as a side effect of the `services.api.main`
# import below, and config.ai_provider is read once at that point — setting
# this any later, e.g. in an autouse fixture, would be too late). Without
# this, a developer with a real GROQ_API_KEY/OPENAI_API_KEY/GEMINI_API_KEY
# in their local .env would have tests that don't explicitly force a
# provider (e.g. hitting /v1/ai/assistant/query with no ?provider= param)
# silently call a real, non-deterministic external API instead of Mock.
os.environ["AI_PROVIDER"] = "mock"

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
