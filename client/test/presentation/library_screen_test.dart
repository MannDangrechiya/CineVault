// CineVault OS — Phase 20: Library & Profile Screen Widget Tests
// Validates rendering of watchlist, watch history, ratings, and user profile analytics

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:drift/native.dart';
import 'package:cinevault_client/data/local/app_database.dart';
import 'package:cinevault_client/data/repositories/personal_offline_repository.dart';
import 'package:cinevault_client/domain/entities/auth_session.dart';
import 'package:cinevault_client/domain/repositories/auth_repository.dart';
import 'package:cinevault_client/presentation/providers/auth_provider.dart';
import 'package:cinevault_client/presentation/screens/library_screen.dart';

class FakeAuthRepository implements AuthRepository {
  AuthSessionEntity? session;

  FakeAuthRepository({this.session});

  @override
  Future<AuthSessionEntity> login(String email, String password) async => session!;

  @override
  Future<void> logout() async {
    session = null;
  }

  @override
  Future<AuthSessionEntity?> getStoredSession() async => session;
}

void main() {
  testWidgets('LibraryScreen renders tabs and analytics metrics', (WidgetTester tester) async {
    final db = AppDatabase(NativeDatabase.memory());
    final offlineRepo = PersonalOfflineRepository(db);

    // Prepopulate some sample offline data
    await offlineRepo.recordOfflineWatchEvent(
      titleId: '018f4a00-0000-7000-8000-000000000001',
      progressPercentage: 100.0,
    );
    await offlineRepo.setOfflineRating(
      titleId: '018f4a00-0000-7000-8000-000000000001',
      ratingValue: 10,
    );
    await offlineRepo.updateOfflineTitleState(
      titleId: '018f4a00-0000-7000-8000-000000000001',
      isFavorite: true,
      manualStatusOverride: 'COMPLETED',
    );

    const mockSession = AuthSessionEntity(
      accessToken: 'jwt_token',
      refreshToken: 'refresh_token',
      userId: 'usr_100',
      email: 'curator@cinevault.org',
      roles: ['curator', 'authenticated_user'],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authProvider.overrideWith((ref) => AuthNotifier(FakeAuthRepository(session: mockSession))),
          personalOfflineRepositoryProvider.overrideWithValue(offlineRepo),
        ],
        child: const MaterialApp(
          home: LibraryScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    // Verify Tab headers
    expect(find.text('My Library'), findsOneWidget);
    expect(find.text('Watchlist'), findsOneWidget);
    expect(find.text('History'), findsOneWidget);
    expect(find.text('Ratings'), findsOneWidget);
    expect(find.text('Analytics'), findsOneWidget);

    // Verify favorite title rendered
    expect(find.textContaining('Title: 018f4a00...'), findsOneWidget);

    // Switch to Analytics tab
    await tester.tap(find.text('Analytics'));
    await tester.pumpAndSettle();

    expect(find.text('curator@cinevault.org'), findsOneWidget);
    expect(find.text('Watch Streak'), findsOneWidget);
    expect(find.text('Total Hours'), findsOneWidget);
    expect(find.text('SIGN OUT'), findsOneWidget);

    await db.close();
  });
}
