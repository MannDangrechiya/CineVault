// CineVault OS — ClubsScreen Widget & Navigation Tests

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cinevault_client/core/theme/app_theme.dart';
import 'package:cinevault_client/domain/entities/social.dart';
import 'package:cinevault_client/domain/repositories/social_repository.dart';
import 'package:cinevault_client/presentation/providers/social_provider.dart';
import 'package:cinevault_client/presentation/screens/clubs_screen.dart';

class FakeSocialRepo implements SocialRepository {
  List<WatchClubEntity> clubsToReturn = const [];
  List<ChallengeEntity> challengesToReturn = const [];

  @override
  Future<List<WatchClubEntity>> listMyClubs() async => clubsToReturn;

  @override
  Future<List<ChallengeEntity>> listActiveChallenges() async => challengesToReturn;

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  const sampleClub = WatchClubEntity(
    clubId: 'club-1',
    name: 'Horror Cinephiles',
    slug: 'horror-cinephiles',
    createdBy: 'user-1',
    description: 'Weekly horror marathons',
    memberCount: 12,
    createdAt: '2026-09-09T00:00:00Z',
  );

  const sampleChallenge = ChallengeEntity(
    challengeId: 'ch-1',
    title: 'Spooktober Marathon',
    description: 'Watch 10 horror movies in October',
    challengeType: 'COUNT',
    goalCount: 10,
    startsAt: '2026-10-01T00:00:00Z',
    endsAt: '2026-10-31T23:59:59Z',
    participantCount: 42,
    myProgress: 3,
  );

  Widget createTestWidget(FakeSocialRepo repo) {
    return ProviderScope(
      overrides: [
        socialRepositoryProvider.overrideWithValue(repo),
      ],
      child: MaterialApp(
        theme: AppTheme.darkTheme,
        home: const ClubsScreen(),
      ),
    );
  }

  testWidgets('Renders clubs list and floating action button when data present', (tester) async {
    final repo = FakeSocialRepo()..clubsToReturn = [sampleClub];

    await tester.pumpWidget(createTestWidget(repo));
    await tester.pumpAndSettle();

    expect(find.text('Watch Clubs'), findsOneWidget);
    expect(find.text('Horror Cinephiles'), findsOneWidget);
    expect(find.text('Weekly horror marathons'), findsOneWidget);
    expect(find.byType(FloatingActionButton), findsOneWidget);
  });

  testWidgets('Shows GlassEmptyState when no clubs joined', (tester) async {
    final repo = FakeSocialRepo()..clubsToReturn = [];

    await tester.pumpWidget(createTestWidget(repo));
    await tester.pumpAndSettle();

    expect(find.text('You have not joined or created any watch clubs yet.'), findsOneWidget);
  });

  testWidgets('Tapping Challenges tab switches view and renders challenges list', (tester) async {
    final repo = FakeSocialRepo()
      ..clubsToReturn = [sampleClub]
      ..challengesToReturn = [sampleChallenge];

    await tester.pumpWidget(createTestWidget(repo));
    await tester.pumpAndSettle();

    // Tap Challenges tab
    await tester.tap(find.text('Challenges'));
    await tester.pumpAndSettle();

    expect(find.text('Spooktober Marathon'), findsOneWidget);
    expect(find.text('Watch 10 horror movies in October'), findsOneWidget);
    expect(find.text('3 / 10'), findsOneWidget);
  });
}
