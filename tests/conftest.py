import os
import sys
from pathlib import Path

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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
    """Yields None. Opt in explicitly (app.dependency_overrides[get_db] =
    override_get_db_fallback) for a test that specifically needs to exercise a
    repository's documented db=None fallback path through the API layer. Not
    applied by default: the suite runs against real Postgres by default so
    tests actually verify real DB behavior (2026-08-29 sizing pass showed only
    10/512 tests depended on the old default-to-None behavior, all due to
    stale hardcoded title UUIDs rather than a real need for the mock path --
    see WEB_FEATURE_AUDIT.md)."""
    yield None

@pytest.fixture(autouse=True)
def configure_test_environment():
    """Ensures no test leaks a get_db override into the ones that run after it."""
    yield
    app.dependency_overrides.pop(get_db, None)
