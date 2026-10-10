// CineVault OS — SettingsScreen Widget Tests

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cinevault_client/core/theme/app_theme.dart';
import 'package:cinevault_client/domain/entities/auth_session.dart';
import 'package:cinevault_client/domain/repositories/auth_repository.dart';
import 'package:cinevault_client/presentation/providers/auth_provider.dart';
import 'package:cinevault_client/presentation/screens/settings_screen.dart';

void main() {
  testWidgets('SettingsScreen renders account info, export formats, and sign-out button', (tester) async {
    const mockSession = AuthSessionEntity(
      accessToken: 'test-token',
      refreshToken: 'test-refresh',
      userId: 'usr-123',
      email: 'curator@cinevault.org',
      roles: ['Curator', 'AuthenticatedUser'],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authProvider.overrideWith((ref) {
            final notifier = AuthNotifier(FakeAuthRepository());
            notifier.state = const AuthState(
              isAuthenticated: true,
              session: mockSession,
            );
            return notifier;
          }),
        ],
        child: MaterialApp(
          theme: AppTheme.darkTheme,
          home: const SettingsScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    // Verify Title & Account info
    expect(find.text('Settings'), findsOneWidget);
    expect(find.text('curator@cinevault.org'), findsOneWidget);
    expect(find.text('Roles: Curator, AuthenticatedUser'), findsOneWidget);

    // Verify Invite & Referral shortcut
    expect(find.text('Invite a Friend & Referral Stats'), findsOneWidget);

    // Verify Data Export options
    expect(find.text('Export Your Data'), findsOneWidget);
    expect(find.text('JSON'), findsOneWidget);
    expect(find.text('CSV'), findsOneWidget);
    expect(find.text('Excel'), findsOneWidget);
    expect(find.text('Markdown'), findsOneWidget);

    // Verify Sign Out button
    expect(find.text('SIGN OUT'), findsOneWidget);
  });
}

class FakeAuthRepository implements AuthRepository {
  @override
  Future<AuthSessionEntity?> getStoredSession() async => null;

  @override
  Future<AuthSessionEntity> login(String email, String password) async {
    throw UnimplementedError();
  }

  @override
  Future<AuthSessionEntity> register(String email, String password, String inviteCode) async {
    throw UnimplementedError();
  }

  @override
  Future<AuthSessionEntity> refreshSession() async {
    throw UnimplementedError();
  }

  @override
  Future<void> logout() async {}
}
