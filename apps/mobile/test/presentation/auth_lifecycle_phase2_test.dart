// CineVault OS — Phase 2: Flutter Native Auth Lifecycle & Security Verification Tests
// Covers:
// 1. Registration mode toggle, invite code validation, and registration submission
// 2. Failed registration error banner handling
// 3. ApiClient 401 transparent token refresh and request retry
// 4. Infinite refresh loop prevention (single retry limit)
// 5. Session restoration on app restart (preserving email, roles, tokens)
// 6. Logout clearing local tokens and local database personal data (CAT-2 user isolation)

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:drift/native.dart';
import 'package:dio/dio.dart';

import 'package:cinevault_client/core/network/api_client.dart';
import 'package:cinevault_client/core/storage/secure_storage.dart';
import 'package:cinevault_client/data/local/app_database.dart';
import 'package:cinevault_client/data/repositories/auth_repository_impl.dart';
import 'package:cinevault_client/domain/entities/auth_session.dart';
import 'package:cinevault_client/domain/repositories/auth_repository.dart';
import 'package:cinevault_client/presentation/providers/auth_provider.dart';
import 'package:cinevault_client/presentation/screens/login_screen.dart';
import 'package:cinevault_client/app.dart';

class MockAuthRepository implements AuthRepository {
  AuthSessionEntity? session;
  final bool failLogin;
  final bool failRegister;
  String? registerEmail;
  String? registerInviteCode;

  MockAuthRepository({
    this.session,
    this.failLogin = false,
    this.failRegister = false,
  });

  @override
  Future<AuthSessionEntity> login(String email, String password) async {
    if (failLogin) {
      throw Exception('Invalid email or password. Please verify demo credentials.');
    }
    final newSession = AuthSessionEntity(
      accessToken: 'access_tok_123',
      refreshToken: 'refresh_tok_123',
      userId: 'usr_mock_1',
      email: email,
      roles: const ['authenticated_user'],
    );
    session = newSession;
    return newSession;
  }

  @override
  Future<AuthSessionEntity> register(String email, String password, String inviteCode) async {
    registerEmail = email;
    registerInviteCode = inviteCode;
    if (failRegister) {
      throw Exception('Invalid or expired invite code. Registration is strictly invite-only.');
    }
    final newSession = AuthSessionEntity(
      accessToken: 'access_tok_reg',
      refreshToken: 'refresh_tok_reg',
      userId: 'usr_mock_reg',
      email: email,
      roles: const ['authenticated_user'],
    );
    session = newSession;
    return newSession;
  }

  @override
  Future<AuthSessionEntity> refreshSession() async {
    if (session == null) throw Exception('No refresh token stored');
    return session!;
  }

  @override
  Future<void> logout() async {
    session = null;
  }

  @override
  Future<AuthSessionEntity?> getStoredSession() async => session;
}

class _MockAdapter implements HttpClientAdapter {
  final Future<ResponseBody> Function(RequestOptions options) handler;
  _MockAdapter(this.handler);

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<List<int>>? requestStream,
    Future<void>? cancelFuture,
  ) {
    return handler(options);
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  FlutterSecureStorage.setMockInitialValues({});

  group('Phase 2 — Registration Flow UI Tests', () {
    testWidgets('Toggles between Sign In and Registration modes', (WidgetTester tester) async {
      final mockRepo = MockAuthRepository();

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            authRepositoryProvider.overrideWithValue(mockRepo),
          ],
          child: const CineVaultApp(),
        ),
      );
      await tester.pumpAndSettle();

      // Initially on Sign In mode
      expect(find.text('SIGN IN'), findsOneWidget);
      expect(find.text('Have an invite code? Register Account'), findsOneWidget);
      expect(find.text('Invite Code'), findsNothing);

      // Tap toggle to register mode
      await tester.tap(find.text('Have an invite code? Register Account'));
      await tester.pumpAndSettle();

      expect(find.text('CREATE ACCOUNT'), findsOneWidget);
      expect(find.text('Register Friend Account (Invite-Only)'), findsOneWidget);
      expect(find.text('Invite Code'), findsOneWidget);
      expect(find.text('Already have an account? Sign In'), findsOneWidget);

      // Toggle back to Sign In mode
      await tester.tap(find.text('Already have an account? Sign In'));
      await tester.pumpAndSettle();

      expect(find.text('SIGN IN'), findsOneWidget);
      expect(find.text('Invite Code'), findsNothing);
    });

    testWidgets('Validates required Invite Code in registration mode', (WidgetTester tester) async {
      final mockRepo = MockAuthRepository();

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            authRepositoryProvider.overrideWithValue(mockRepo),
          ],
          child: const CineVaultApp(),
        ),
      );
      await tester.pumpAndSettle();

      // Switch to register mode
      await tester.tap(find.text('Have an invite code? Register Account'));
      await tester.pumpAndSettle();

      // Try submitting with empty invite code
      await tester.tap(find.text('CREATE ACCOUNT'));
      await tester.pumpAndSettle();

      expect(find.text('Invite code is required for registration.'), findsOneWidget);
      expect(find.byType(MainShellScreen), findsNothing);
    });

    testWidgets('Successful registration transitions to MainShellScreen', (WidgetTester tester) async {
      final mockRepo = MockAuthRepository();

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            authRepositoryProvider.overrideWithValue(mockRepo),
          ],
          child: const CineVaultApp(),
        ),
      );
      await tester.pumpAndSettle();

      // Switch to register mode
      await tester.tap(find.text('Have an invite code? Register Account'));
      await tester.pumpAndSettle();

      // Enter valid fields
      await tester.enterText(find.byType(TextFormField).at(0), 'friend@cinevault.local');
      await tester.enterText(find.byType(TextFormField).at(1), 'friendpass123');
      await tester.enterText(find.byType(TextFormField).at(2), 'inv_valid_code');

      await tester.tap(find.text('CREATE ACCOUNT'));
      await tester.pumpAndSettle();

      expect(mockRepo.registerEmail, equals('friend@cinevault.local'));
      expect(mockRepo.registerInviteCode, equals('inv_valid_code'));
      expect(find.byType(MainShellScreen), findsOneWidget);
      expect(find.byType(LoginScreen), findsNothing);
    });

    testWidgets('Failed registration with invalid invite displays error banner', (WidgetTester tester) async {
      final mockRepo = MockAuthRepository(failRegister: true);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            authRepositoryProvider.overrideWithValue(mockRepo),
          ],
          child: const CineVaultApp(),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Have an invite code? Register Account'));
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(TextFormField).at(0), 'friend@cinevault.local');
      await tester.enterText(find.byType(TextFormField).at(1), 'friendpass123');
      await tester.enterText(find.byType(TextFormField).at(2), 'inv_expired_code');

      await tester.tap(find.text('CREATE ACCOUNT'));
      await tester.pumpAndSettle();

      expect(find.byType(LoginScreen), findsOneWidget);
      expect(find.textContaining('Invalid or expired invite code'), findsOneWidget);
      expect(find.byType(MainShellScreen), findsNothing);
    });
  });

  group('Phase 2 — Token Refresh & Retry Lifecycle', () {
    test('ApiClient refreshes token on 401 and replays original request', () async {
      final fakeStorage = SecureStorageService();
      await fakeStorage.saveTokens(
        accessToken: 'expired_access_token',
        refreshToken: 'valid_refresh_token',
        userId: 'usr_test_1',
      );

      final dio = Dio(BaseOptions(baseUrl: 'http://127.0.0.1:8000'));
      final refreshDio = Dio(BaseOptions(baseUrl: 'http://127.0.0.1:8000'));

      int mainRequestCount = 0;
      int refreshRequestCount = 0;

      dio.httpClientAdapter = _MockAdapter((options) async {
        mainRequestCount++;
        if (options.extra['_retry'] == true) {
          // Verify that new token was injected on retry
          expect(options.headers['Authorization'], equals('Bearer new_valid_access_token'));
          return ResponseBody.fromString(
            '{"items": [{"title_id": "mov_1"}]}',
            200,
            headers: {
              Headers.contentTypeHeader: [Headers.jsonContentType],
            },
          );
        } else {
          return ResponseBody.fromString(
            '{"detail": "Token expired"}',
            401,
            headers: {
              Headers.contentTypeHeader: [Headers.jsonContentType],
            },
          );
        }
      });

      refreshDio.httpClientAdapter = _MockAdapter((options) async {
        refreshRequestCount++;
        return ResponseBody.fromString(
          '{"access_token": "new_valid_access_token", "refresh_token": "new_valid_refresh_token", "user_id": "usr_test_1", "email": "user@cinevault.local", "roles": ["authenticated_user"]}',
          200,
          headers: {
            Headers.contentTypeHeader: [Headers.jsonContentType],
          },
        );
      });

      final apiClient = ApiClient(
        dio: dio,
        tokenRefreshDio: refreshDio,
        secureStorage: fakeStorage,
      );

      // Make a request that will initially get 401, refresh, and then succeed on retry
      final response = await apiClient.dio.get('/v1/titles');

      expect(response.statusCode, equals(200));
      expect(response.data['items'], isNotEmpty);
      expect(refreshRequestCount, equals(1));
      expect(mainRequestCount, equals(2));

      // Verify that new tokens were persisted in secure storage
      final storedAccess = await fakeStorage.getAccessToken();
      final storedRefresh = await fakeStorage.getRefreshToken();
      expect(storedAccess, equals('new_valid_access_token'));
      expect(storedRefresh, equals('new_valid_refresh_token'));
    });

    test('ApiClient does not loop infinitely if retried request still returns 401', () async {
      final fakeStorage = SecureStorageService();
      await fakeStorage.saveTokens(
        accessToken: 'bad_token',
        refreshToken: 'bad_refresh',
        userId: 'usr_test_2',
      );

      final dio = Dio(BaseOptions(baseUrl: 'http://127.0.0.1:8000'));
      final refreshDio = Dio(BaseOptions(baseUrl: 'http://127.0.0.1:8000'));

      bool unauthorizedCallbackFired = false;
      int requestAttempts = 0;

      dio.httpClientAdapter = _MockAdapter((options) async {
        requestAttempts++;
        return ResponseBody.fromString(
          '{"detail": "Still unauthorized"}',
          401,
          headers: {
            Headers.contentTypeHeader: [Headers.jsonContentType],
          },
        );
      });

      refreshDio.httpClientAdapter = _MockAdapter((options) async {
        return ResponseBody.fromString(
          '{"access_token": "new_access", "refresh_token": "new_refresh", "user_id": "usr_test_2"}',
          200,
          headers: {
            Headers.contentTypeHeader: [Headers.jsonContentType],
          },
        );
      });

      final apiClient = ApiClient(
        dio: dio,
        tokenRefreshDio: refreshDio,
        secureStorage: fakeStorage,
        onUnauthorized: () {
          unauthorizedCallbackFired = true;
        },
      );

      try {
        await apiClient.dio.get('/v1/personal/history');
      } catch (_) {}

      // Initial request + 1 retry = exactly 2 attempts, NO infinite loop
      expect(requestAttempts, equals(2));
      expect(unauthorizedCallbackFired, isTrue);

      // Session must be wiped
      final token = await fakeStorage.getAccessToken();
      expect(token, isNull);
    });
  });

  group('Phase 2 — App Restart & User Isolation Tests', () {
    test('Session restoration preserves user email, roles, and tokens on app restart', () async {
      final fakeStorage = SecureStorageService();
      final db = AppDatabase(NativeDatabase.memory());

      // Simulate a curator logging in and persisting session
      final repo = AuthRepositoryImpl(
        secureStorage: fakeStorage,
        db: db,
      );

      await fakeStorage.saveTokens(
        accessToken: 'test_access_jwt',
        refreshToken: 'test_refresh_jwt',
        userId: 'usr_curator_10',
        email: 'curator@cinevault.local',
        roles: ['curator', 'authenticated_user'],
      );

      // Simulate app restart: re-instantiate repo and query getStoredSession()
      final restartedRepo = AuthRepositoryImpl(
        secureStorage: fakeStorage,
        db: db,
      );

      final session = await restartedRepo.getStoredSession();
      expect(session, isNotNull);
      expect(session!.userId, equals('usr_curator_10'));
      expect(session.email, equals('curator@cinevault.local'));
      expect(session.roles, contains('curator'));
      expect(session.roles, contains('authenticated_user'));
      expect(session.accessToken, equals('test_access_jwt'));
    });

    test('Logout clears session and wipes local database personal data (User Isolation)', () async {
      final fakeStorage = SecureStorageService();
      final db = AppDatabase(NativeDatabase.memory());

      final repo = AuthRepositoryImpl(
        secureStorage: fakeStorage,
        db: db,
      );

      // User A records local mutations and personal data
      await fakeStorage.saveTokens(
        accessToken: 'user_a_token',
        refreshToken: 'user_a_refresh',
        userId: 'usr_user_a',
        email: 'user_a@cinevault.local',
        roles: ['authenticated_user'],
      );

      await db.insertMutation(
        OutboxMutationsCompanion.insert(
          mutationId: 'mut_a_001',
          mutationType: 'CREATE_WATCH_EVENT',
          clientTimestamp: DateTime.now().toUtc().toIso8601String(),
          payloadJson: '{"title_id": "mov_parasite"}',
        ),
      );
      await db.upsertOfflineWatchEvent(
        OfflineWatchEventsCompanion.insert(
          watchEventId: 'ev_a_001',
          titleId: 'mov_parasite',
          watchedAt: DateTime.now().toUtc().toIso8601String(),
        ),
      );

      expect((await db.getPendingMutations()).length, equals(1));
      expect((await db.getOfflineWatchEvents()).length, equals(1));

      // User A logs out
      await repo.logout();

      // Session tokens must be cleared
      expect(await fakeStorage.getAccessToken(), isNull);
      expect(await fakeStorage.getRefreshToken(), isNull);
      expect(await fakeStorage.getUserId(), isNull);
      expect(await repo.getStoredSession(), isNull);

      // Local outbox mutations and personal history must be completely wiped
      // ensuring User B cannot submit User A's mutations or view User A's data
      expect((await db.getPendingMutations()).isEmpty, isTrue);
      expect((await db.getOfflineWatchEvents()).isEmpty, isTrue);
    });
  });
}
