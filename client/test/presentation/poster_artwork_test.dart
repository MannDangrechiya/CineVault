// CineVault OS — Poster Artwork & Fallback Icon Widget Tests (Phase 9.2)

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cinevault_client/domain/entities/title.dart';
import 'package:cinevault_client/presentation/screens/catalog_screen.dart';
import 'package:cinevault_client/presentation/providers/catalog_provider.dart';
import 'package:cinevault_client/data/remote/titles_remote_datasource.dart';

class MockPosterTitlesDatasource implements TitlesRemoteDatasource {
  final List<CanonicalTitleEntity> mockTitles;

  MockPosterTitlesDatasource(this.mockTitles);

  @override
  Future<List<CanonicalTitleEntity>> listTitles({
    int limit = 20,
    String? cursor,
    String? contentType,
    int? productionYear,
    String? originCountry,
  }) async => mockTitles;

  @override
  Future<CanonicalTitleEntity> getTitleDetail(String titleId) async => mockTitles.first;

  @override
  Future<List<AvailabilityEntity>> getTitleAvailability(String titleId) async => [];

  @override
  Future<List<ReleaseEntity>> getTitleReleases(String titleId) async => [];
}

void main() {
  testWidgets('Renders fallback icon when posterUrl is null', (WidgetTester tester) async {
    const titleWithoutPoster = CanonicalTitleEntity(
      titleId: 'test-1',
      displayId: 'MOV-000001',
      primaryTitle: 'No Poster Movie',
      contentType: 'MOVIE',
      releaseYear: 2024,
      posterUrl: null,
      genres: ['Drama'],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          titlesRemoteDatasourceProvider.overrideWithValue(MockPosterTitlesDatasource([titleWithoutPoster])),
        ],
        child: const MaterialApp(home: CatalogScreen()),
      ),
    );

    await tester.pumpAndSettle();

    // Expect Icons.movie fallback icon present, no Image widget
    expect(find.byIcon(Icons.movie), findsOneWidget);
    expect(find.byType(Image), findsNothing);
  });

  testWidgets('Renders Image.network when posterUrl is present', (WidgetTester tester) async {
    const titleWithPoster = CanonicalTitleEntity(
      titleId: 'test-2',
      displayId: 'MOV-000002',
      primaryTitle: 'Poster Movie',
      contentType: 'MOVIE',
      releaseYear: 2024,
      posterUrl: 'https://cdn.cinevault.org/artwork/posters/mov-000002.jpg',
      genres: ['Action'],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          titlesRemoteDatasourceProvider.overrideWithValue(MockPosterTitlesDatasource([titleWithPoster])),
        ],
        child: const MaterialApp(home: CatalogScreen()),
      ),
    );

    await tester.pump();

    // Expect Image widget present for posterUrl
    expect(find.byType(Image), findsOneWidget);
  });
}
