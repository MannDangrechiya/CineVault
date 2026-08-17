## Gap Closed
> "services/api/ingestion/adapters.py defines KobisProviderAdapter and TvdbProviderAdapter with hardcoded mock responses. No live HTTP acquisition adapter is implemented."

## Summary of Changes
1. **Configuration (`config.py` & `.env.example`)**: Added `ingestion_mode`, `kobis_api_key`, and `tvdb_api_key` configuration parameters and documented `INGESTION_MODE=mock|live`, `KOBIS_API_KEY`, and `TVDB_API_KEY` in `.env.example`.
2. **Live KOBIS Adapter (`adapters.py`)**: Implemented `KobisProviderAdapter` using `httpx.AsyncClient` targeting `http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieInfo.json` with up to 3 exponential backoff retries and normalization schema mappings.
3. **Live TVDB Adapter (`adapters.py`)**: Implemented `TvdbProviderAdapter` using `httpx.AsyncClient` targeting `https://api4.thetvdb.com/v4/` with bearer authentication via `POST /login`, `/series/{id}`, `/movies/{id}`, 3 exponential backoff retries, and normalization schema mappings.
4. **Unit & Safety Tests (`test_ingestion_live_adapters.py`)**: Added test suite verifying live endpoint parsing, auth login, retry resilience, and schema normalization with `httpx` response mocks.

## Test Evidence
- **Backend Test (`python -m pytest -v`)**: 147 passed, 0 failures (100% pass rate).
- **Flutter Analysis (`flutter analyze`)**: No issues found!
- **Flutter Test (`flutter test`)**: 17 passed, 0 failures.

## Follow-up / Next Phases
- Phase 9.7: Control Room curator screen in Flutter.
