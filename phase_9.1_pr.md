## Gap Closed
> "client/lib/data/remote/titles_remote_datasource.dart sends query params `year` and `country`, but services/api/routers/titles.py (and its Pydantic query schema) expects `production_year` and `origin_country`. Because FastAPI ignores unknown query params by default, the year/country filters silently no-op instead of erroring — catalog filtering appears broken with no visible cause."

## Summary of Changes
1. **Client (`TitlesRemoteDatasource`)**: Updated parameter names and query dictionary keys from `year` & `country` to `production_year` and `origin_country` in `client/lib/data/remote/titles_remote_datasource.dart`.
2. **Client (`CatalogProvider` & `CatalogState`)**: Threaded `productionYear` and `originCountry` parameters into `CatalogNotifier.fetchTitles()` and updated `CatalogState`.
3. **Client Unit Test**: Added `client/test/data/titles_remote_datasource_test.dart` asserting that `production_year` and `origin_country` query parameters are sent on HTTP GET requests.
4. **Backend Contract Test**: Added `test_list_titles_filter_contract` in `tests/test_contracts.py` asserting that `GET /v1/titles?production_year=2019&origin_country=KR` correctly filters titles.

## Test Evidence
- **Backend (`python -m pytest -v`)**: 128 passed, 0 failures (100% pass rate).
- **Flutter Analysis (`flutter analyze`)**: No issues found!
- **Flutter Test (`flutter test`)**: 15 passed, 0 failures.

## Follow-up / Next Phases
- Phase 9.2: Replace placeholder icons with real poster/backdrop artwork across `CatalogScreen`, `SearchScreen`, and `TitleDetailScreen`.
