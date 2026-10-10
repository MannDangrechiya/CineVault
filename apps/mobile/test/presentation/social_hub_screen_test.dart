// CineVault OS — SocialHubScreen Widget & Tab Navigation Tests

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cinevault_client/core/theme/app_theme.dart';
import 'package:cinevault_client/domain/entities/social.dart';
import 'package:cinevault_client/domain/repositories/social_repository.dart';
import 'package:cinevault_client/presentation/providers/social_provider.dart';
import 'package:cinevault_client/presentation/screens/social_hub_screen.dart';

class FakeSocialRepo implements SocialRepository {
  List<FriendshipEntity> friendshipsToReturn = const [];
  LeaderboardEntity? leaderboardToReturn;
  List<RecommendationEntity> recommendationsToReturn = const [];

  @override
  Future<List<FriendshipEntity>> getFriendships() async => friendshipsToReturn;

  @override
  Future<LeaderboardEntity> getSocialLeaderboard({String period = 'weekly'}) async {
    return leaderboardToReturn ??
        const LeaderboardEntity(
          period: 'weekly',
          entries: [],
          calculatedAt: '2026-09-09T00:00:00Z',
        );
  }

  @override
  Future<List<RecommendationEntity>> getRecommendations({String? role}) async {
    return recommendationsToReturn;
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  const sampleLeaderboard = LeaderboardEntity(
    period: 'weekly',
    calculatedAt: '2026-09-09T00:00:00Z',
    entries: [
      LeaderboardEntryEntity(
        userId: 'usr-1',
        name: 'Cinema Buff',
        username: 'cinemabuff',
        watchCount: 14,
        watchHours: 28.5,
        rank: 1,
        isCurrentUser: true,
      ),
    ],
  );

  Widget createTestWidget(FakeSocialRepo repo) {
    return ProviderScope(
      overrides: [
        socialRepositoryProvider.overrideWithValue(repo),
      ],
      child: MaterialApp(
        theme: AppTheme.darkTheme,
        home: const SocialHubScreen(),
      ),
    );
  }

  testWidgets('SocialHubScreen renders tabs and empty state for new user', (tester) async {
    final repo = FakeSocialRepo();

    await tester.pumpWidget(createTestWidget(repo));
    await tester.pumpAndSettle();

    // Verify Tab switcher buttons
    expect(find.text('Social Hub'), findsOneWidget);
    expect(find.text('Friends'), findsOneWidget);
    expect(find.text('Leaderboard'), findsOneWidget);
    expect(find.text('Recommendations'), findsOneWidget);

    // Verify GlassEmptyState message on Friends tab
    expect(find.text('No friends yet. Send a friend request to get started.'), findsOneWidget);
  });

  testWidgets('Switching to Leaderboard tab displays rank and user metrics', (tester) async {
    final repo = FakeSocialRepo()..leaderboardToReturn = sampleLeaderboard;

    await tester.pumpWidget(createTestWidget(repo));
    await tester.pumpAndSettle();

    // Tap Leaderboard tab
    await tester.tap(find.text('Leaderboard'));
    await tester.pumpAndSettle();

    expect(find.text('Cinema Buff'), findsOneWidget);
    expect(find.text('#1'), findsOneWidget);
    expect(find.text('14 watched • 28.5 hrs'), findsOneWidget);
    expect(find.text('You'), findsOneWidget);
  });
}
