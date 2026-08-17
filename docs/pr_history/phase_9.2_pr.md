## Gap Closed
> "CatalogScreen, SearchScreen, and TitleDetailScreen currently render Icon(Icons.movie) / Icon(Icons.tv) inside grey containers instead of loading artwork."

## Summary of Changes
1. **Domain Entity (`title.dart`)**: Added `backdropUrl` field and updated JSON deserialization/serialization in `CanonicalTitleEntity`.
2. **CatalogScreen (`catalog_screen.dart`)**: Replaced static icon placeholders with `Image.network(title.posterUrl)`, loading indicator, and fallback `Icon(Icons.movie)`/`Icon(Icons.tv)` on `errorBuilder`.
3. **SearchScreen (`search_screen.dart`)**: Updated `ListTile` leading avatar to render poster image thumbnail when `posterUrl` is available, with icon fallback.
4. **TitleDetailScreen (`title_detail_screen.dart`)**: Updated header poster container to render artwork image with loading indicator and fallback icon.
5. **Widget Tests (`poster_artwork_test.dart`)**: Added widget test asserting fallback icon when `posterUrl` is null and `Image.network` widget when `posterUrl` is present.

## Test Evidence
- **Flutter Analysis (`flutter analyze`)**: No issues found! (ran in 7.4s).
- **Flutter Test (`flutter test`)**: 17 passed, 0 failures.
- **Backend Test (`python -m pytest -v`)**: 128 passed, 0 failures.

## Follow-up / Next Phases
- Phase 9.4: Implement real OpenAI provider adapter for AI Assistant.
