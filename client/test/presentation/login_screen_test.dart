// CineVault OS — Login Screen & Auth Flow Widget Tests (Phase 9.8)

import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:cinevault_client/domain/entities/auth_session.dart';
import 'package:cinevault_client/domain/repositories/auth_repository.dart';
import 'package:cinevault_client/presentation/providers/auth_provider.dart';
import 'package:cinevault_client/presentation/screens/login_screen.dart';
import 'package:cinevault_client/app.dart';

class FakeAuthRepository implements AuthRepository {
  AuthSessionEntity? session;
  final bool shouldFail;

  FakeAuthRepository({this.session, this.shouldFail = false});

  @override
  Future<AuthSessionEntity> login(String email, String password) async {
    if (shouldFail) {
      throw Exception('Invalid credentials');
    }
    final newSession = AuthSessionEntity(
      accessToken: 'mock_jwt_token_123',
      refreshToken: 'mock_refresh_token_123',
      userId: 'usr_001',
      email: email,
      roles: const ['authenticated_user'],
    );
    session = newSession;
    return newSession;
  }

  @override
  Future<void> logout() async {
    session = null;
  }

  @override
  Future<AuthSessionEntity?> getStoredSession() async => session;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  FlutterSecureStorage.setMockInitialValues({});

  testWidgets('Renders LoginScreen when unauthenticated', (WidgetTester tester) async {
    final fakeRepo = FakeAuthRepository(session: null);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authRepositoryProvider.overrideWithValue(fakeRepo),
        ],
        child: const CineVaultApp(),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.byType(LoginScreen), findsOneWidget);
    expect(find.text('CineVault OS'), findsAtLeast(1));
    expect(find.text('SIGN IN'), findsOneWidget);
  });

  testWidgets('Successful login stores token and navigates to App Shell', (WidgetTester tester) async {
    final fakeRepo = FakeAuthRepository(session: null);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authRepositoryProvider.overrideWithValue(fakeRepo),
        ],
        child: const CineVaultApp(),
      ),
    );

    await tester.pumpAndSettle();

    await tester.tap(find.text('SIGN IN'));
    await tester.pumpAndSettle();

    // After login success, root gate renders MainShellScreen
    expect(find.byType(MainShellScreen), findsOneWidget);
    expect(find.byType(LoginScreen), findsNothing);
  });

  testWidgets('Failed login displays error banner and remains on LoginScreen', (WidgetTester tester) async {
    final fakeRepo = FakeAuthRepository(session: null, shouldFail: true);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authRepositoryProvider.overrideWithValue(fakeRepo),
        ],
        child: const CineVaultApp(),
      ),
    );

    await tester.pumpAndSettle();

    await tester.tap(find.text('SIGN IN'));
    await tester.pumpAndSettle();

    expect(find.byType(LoginScreen), findsOneWidget);
    expect(find.text('Invalid credentials or login failed.'), findsOneWidget);
  });

  testWidgets('401 mid-session error bounces back to LoginScreen', (WidgetTester tester) async {
    const activeSession = AuthSessionEntity(
      accessToken: 'active_token',
      refreshToken: 'ref_token',
      userId: 'usr_active',
      email: 'user@cinevault.org',
      roles: ['authenticated_user'],
    );
    final fakeRepo = FakeAuthRepository(session: activeSession);

    final container = ProviderContainer(
      overrides: [
        authRepositoryProvider.overrideWithValue(fakeRepo),
      ],
    );

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: const CineVaultApp(),
      ),
    );

    await tester.pumpAndSettle();

    // Verified initially logged in
    expect(find.byType(MainShellScreen), findsOneWidget);

    // Simulate 401 mid-session bounce
    container.read(authProvider.notifier).handle401Unauthorized();
    await tester.pumpAndSettle();

    expect(find.byType(LoginScreen), findsOneWidget);
    expect(find.text('Authentication session expired. Please log in again.'), findsOneWidget);
  });
}
