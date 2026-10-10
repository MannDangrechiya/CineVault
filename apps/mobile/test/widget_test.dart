// CineVault OS — Main Shell Widget Unit Tests

import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cinevault_client/app.dart';
import 'package:cinevault_client/presentation/providers/auth_provider.dart';
import 'package:cinevault_client/presentation/providers/catalog_provider.dart';
import 'package:cinevault_client/presentation/providers/recommendation_provider.dart';
import 'package:cinevault_client/data/remote/titles_remote_datasource.dart';
import 'package:cinevault_client/data/remote/recommendations_remote_datasource.dart';
import 'package:cinevault_client/domain/entities/auth_session.dart';
import 'package:cinevault_client/domain/entities/title.dart';
import 'package:cinevault_client/domain/entities/recommendation.dart';
import 'package:cinevault_client/domain/repositories/auth_repository.dart';

class FakeTitlesRemoteDatasource implements TitlesRemoteDatasource {
  @override
  Future<List<CanonicalTitleEntity>> listTitles({
    int limit = 20,
    String? cursor,
    String? contentType,
    int? productionYear,
    String? originCountry,
  }) async {
    return [
      const CanonicalTitleEntity(
        titleId: 'test-title-1',
        displayId: 'MOV-000001',
        primaryTitle: 'Test Movie',
        contentType: 'MOVIE',
        releaseYear: 2024,
        genres: ['Action'],
      ),
    ];
  }

  @override
  Future<CanonicalTitleEntity> getTitleDetail(String titleId) async {
    return const CanonicalTitleEntity(
      titleId: 'test-title-1',
      displayId: 'MOV-000001',
      primaryTitle: 'Test Movie',
      contentType: 'MOVIE',
      releaseYear: 2024,
      genres: ['Action'],
    );
  }

  @override
  Future<List<AvailabilityEntity>> getTitleAvailability(String titleId) async => [];

  @override
  Future<List<ReleaseEntity>> getTitleReleases(String titleId) async => [];
}

class FakeRecommendationsRemoteDatasource implements RecommendationsRemoteDatasource {
  @override
  Future<List<RecommendationItemEntity>> getPersonalizedRecommendations({
    String mode = 'tonight',
    int? maxRuntime,
    String? genre,
    bool availableOnly = true,
    bool includeWatched = false,
    String? seedTitleId,
    int limit = 10,
  }) async => [];

  @override
  Future<List<RecommendationItemEntity>> getColdStartRecommendations({
    List<String>? preferredGenres,
    List<String>? preferredCountries,
    List<String>? preferredLanguages,
    int? minReleaseYear,
    int? maxReleaseYear,
    int limit = 10,
  }) async => [];

  @override
  Future<List<RecommendationItemEntity>> getSimilarTitles(String titleId, {int limit = 5}) async => [];

  @override
  Future<GroundedExplanationEntity> explainRecommendation({
    required String titleId,
    String? seedTitleId,
  }) async => const GroundedExplanationEntity(
        explanationText: 'Test explanation',
        matchedGenres: [],
        matchedDirectors: [],
        matchedActors: [],
      );
}

class FakeAuthRepository implements AuthRepository {
  AuthSessionEntity? session;

  FakeAuthRepository({this.session});

  @override
  Future<AuthSessionEntity> login(String email, String password) async {
    session = AuthSessionEntity(
      accessToken: 'mock_jwt_token',
      refreshToken: 'mock_refresh_token',
      userId: 'usr_001',
      email: email,
      roles: const ['authenticated_user'],
    );
    return session!;
  }

  @override
  Future<AuthSessionEntity> register(String email, String password, String inviteCode) async {
    return login(email, password);
  }

  @override
  Future<AuthSessionEntity> refreshSession() async {
    if (session == null) throw Exception('No session stored');
    return session!;
  }

  @override
  Future<void> logout() async {
    session = null;
  }

  @override
  Future<AuthSessionEntity?> getStoredSession() async => session;
}

void main() {
  testWidgets('CineVaultApp shell displays navigation bar tabs', (WidgetTester tester) async {
    const mockSession = AuthSessionEntity(
      accessToken: 'mock_jwt_token',
      refreshToken: 'mock_refresh_token',
      userId: 'usr_001',
      email: 'user@cinevault.org',
      roles: ['authenticated_user'],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authProvider.overrideWith((ref) => AuthNotifier(FakeAuthRepository(session: mockSession))),
          titlesRemoteDatasourceProvider.overrideWithValue(FakeTitlesRemoteDatasource()),
          recommendationsRemoteDatasourceProvider.overrideWithValue(FakeRecommendationsRemoteDatasource()),
        ],
        child: const CineVaultApp(),
      ),
    );

    await tester.pumpAndSettle();

    // Verify app title and navigation bar labels exist
    expect(find.text('CineVault Catalog'), findsOneWidget);
    expect(find.text('Catalog'), findsOneWidget);
    expect(find.text('Search'), findsOneWidget);
    expect(find.text('For You'), findsOneWidget);
    expect(find.text('Assistant'), findsOneWidget);
    expect(find.text('Library'), findsOneWidget);
    expect(find.text('Outbox'), findsOneWidget);
  });
}
