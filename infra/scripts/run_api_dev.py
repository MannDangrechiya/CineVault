# CineVault OS — Dev API server launcher (uvicorn --reload Windows fix)
#
# `python -m uvicorn ... --reload` on Windows has been flaky on this machine:
# it sometimes logs "Reloading..." but never actually spawns a new worker, or
# the whole process silently disappears (see WEB_FEATURE_AUDIT.md). Root
# cause is Windows' default ProactorEventLoop conflicting with the reload
# supervisor's subprocess/signal handling. The fix has to run BEFORE uvicorn
# creates its event loop — setting the policy inside the app module itself is
# too late, since the reload supervisor process starts before it ever imports
# the app. This script sets the policy first, then starts uvicorn.
#
# Usage: python infra/scripts/run_api_dev.py [--port 8000] [--no-reload]

import argparse
import asyncio
import os
import sys
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Ensure the repo root is on sys.path so "services.api.main:app" resolves
# regardless of the working directory this script is launched from.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import uvicorn  # noqa: E402  (must come after the event loop policy is set)


def main() -> None:
    parser = argparse.ArgumentParser(description="CineVault OS API dev server")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    args = parser.parse_args()

    os.environ.setdefault("ENVIRONMENT", "local_development")

    uvicorn.run(
        "services.api.main:app",
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
        reload_dirs=[str(REPO_ROOT / "services" / "api")],
        app_dir=str(REPO_ROOT),
    )


if __name__ == "__main__":
    main()
