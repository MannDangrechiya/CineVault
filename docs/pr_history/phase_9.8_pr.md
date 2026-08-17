## Gap Closed
> "Client relies on hardcoded pre-generated JWTs with no login UI, token persistence lifecycle, 401 unauthenticated bounce-back routing, or logout action."

## Summary of Changes
1. **Backend Auth Router (`auth.py` & `main.py`)**: Added `POST /v1/auth/login` endpoint issuing valid OIDC-compliant JWT tokens containing claims (`iss`, `aud`, `exp`, `sub`, `email`, `roles`).
2. **Domain & Data Layers (`auth_session.dart`, `auth_remote_datasource.dart`, `auth_repository_impl.dart`)**: Built domain entity and data layer for authenticating credentials, storing JWT tokens securely via `SecureStorageService`, and retrieving active sessions.
3. **State Management & Provider (`auth_provider.dart`)**: Added `AuthNotifier` managing login state, session checking, logout, and 401 unauthenticated error reset.
4. **UI Screen (`login_screen.dart`)**: Created dark theme login screen with email/password inputs, loading spinner, error banner, and quick demo credentials buttons.
5. **Auth Gate & App Shell (`app.dart` & `api_client.dart`)**: Added `RootAuthGate` enforcing `LoginScreen()` display when unauthenticated, added Logout action button to shell header, and wired `ApiClient` 401 interceptor callback to clear session and route to login on expired tokens.
6. **Widget & Auth Flow Tests (`login_screen_test.dart` & `widget_test.dart`)**: Added comprehensive widget test suite covering login form rendering, token storage, successful catalog navigation, failed login error display, and 401 mid-session bounce-back.

## Test Evidence
- **Backend Tests (`python -m pytest -v`)**: 147 passed, 0 failures.
- **Flutter Analysis (`flutter analyze`)**: No issues found!
- **Flutter Unit & Widget Tests (`flutter test`)**: 24 passed, 0 failures.

## Follow-up / Next Phases
- Phase 9.9: Auto-sync on reconnect (ADR-004 client outbox sync).
