// CineVault OS — Main Shell Widget Unit Tests

import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cinevault_client/app.dart';
import 'package:cinevault_client/presentation/providers/catalog_provider.dart';
import 'package:cinevault_client/presentation/providers/recommendation_provider.dart';
import 'package:cinevault_client/data/remote/titles_remote_datasource.dart';
import 'package:cinevault_client/data/remote/recommendations_remote_datasource.dart';
import 'package:cinevault_client/domain/entities/title.dart';
import 'package:cinevault_client/domain/entities/recommendation.dart';

class FakeTitlesRemoteDatasource implements TitlesRemoteDatasource {
  @override
  Future<List<CanonicalTitleEntity>> listTitles({
    int limit = 20,
    String? cursor,
    String? contentType,
    int? year,
    String? country,
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
    required List<String> preferredGenres,
    required List<String> seedTitleIds,
    int limit = 10,
  }) async => [];

  @override
  Future<List<RecommendationItemEntity>> getSimilarTitles(String titleId, {int limit = 5}) async => [];

  @override
  Future<GroundedExplanationEntity> explainRecommendation({
    required String titleId,
    String? seedTitleId,
  }) async => const GroundedExplanationEntity(
        overallScore: 0.9,
        contentSimilarityScore: 0.9,
        tasteFitScore: 0.9,
        popularityScore: 0.9,
        textualExplanation: 'Test explanation',
        citations: [],
      );
}

void main() {
  testWidgets('CineVaultApp shell displays navigation bar tabs', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
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
    expect(find.text('Outbox'), findsOneWidget);
  });
}
