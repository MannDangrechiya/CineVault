// CineVault OS — Social Riverpod Providers (Part 3.1)
// Friendships, leaderboard, badges & referrals reads used across the social
// hub, dashboard, and invite screens. Screen-specific state (pick-room
// voting, club membership, challenge progress) lives alongside those screens
// and calls through socialRepositoryProvider directly.

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/remote/social_remote_datasource.dart';
import '../../data/repositories/social_repository_impl.dart';
import '../../domain/entities/social.dart';
import '../../domain/repositories/social_repository.dart';
import 'catalog_provider.dart' show apiClientProvider;

final socialRemoteDatasourceProvider = Provider<SocialRemoteDatasource>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return SocialRemoteDatasource(apiClient: apiClient);
});

final socialRepositoryProvider = Provider<SocialRepository>((ref) {
  final remoteDatasource = ref.watch(socialRemoteDatasourceProvider);
  return SocialRepositoryImpl(remoteDatasource: remoteDatasource);
});

/// Accepted + pending friendships for the current user.
final friendshipsProvider = FutureProvider.autoDispose<List<FriendshipEntity>>((ref) {
  return ref.watch(socialRepositoryProvider).getFriendships();
});

final acceptedFriendsProvider = Provider.autoDispose<List<FriendshipEntity>>((ref) {
  final async = ref.watch(friendshipsProvider);
  final friends = async.asData?.value ?? const <FriendshipEntity>[];
  return friends.where((f) => f.status == 'ACCEPTED').toList();
});

/// Taste-match leaderboard for a given period ('weekly' | 'monthly' | 'all_time').
final socialLeaderboardProvider =
    FutureProvider.autoDispose.family<LeaderboardEntity, String>((ref, period) {
  return ref.watch(socialRepositoryProvider).getSocialLeaderboard(period: period);
});

final userBadgesProvider = FutureProvider.autoDispose<UserBadgesEntity>((ref) {
  return ref.watch(socialRepositoryProvider).getUserBadges();
});

final referralStatsProvider = FutureProvider.autoDispose<ReferralStatsEntity>((ref) {
  return ref.watch(socialRepositoryProvider).getReferralStats();
});

/// Recommendations sent to / received by the current user ('sent' | 'received' | 'all').
final recommendationsInboxProvider =
    FutureProvider.autoDispose.family<List<RecommendationEntity>, String>((ref, role) {
  return ref.watch(socialRepositoryProvider).getRecommendations(role: role);
});

final myClubsProvider = FutureProvider.autoDispose<List<WatchClubEntity>>((ref) {
  return ref.watch(socialRepositoryProvider).listMyClubs();
});

final activeChallengesProvider = FutureProvider.autoDispose<List<ChallengeEntity>>((ref) {
  return ref.watch(socialRepositoryProvider).listActiveChallenges();
});
