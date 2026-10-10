// CineVault OS — Social Repository Interface (Part 3.1)

import '../entities/social.dart';

abstract class SocialRepository {
  // Friendships
  Future<List<FriendshipEntity>> getFriendships();
  Future<FriendshipEntity> sendFriendRequest(String addresseeId);
  Future<FriendshipEntity> updateFriendshipStatus({required String friendshipId, required String status});
  Future<void> deleteFriendship(String friendshipId);
  Future<CompatibilityEntity> getFriendCompatibility(String friendId);
  Future<List<TasteMatchEntity>> getTasteMatches({int limit});

  // Peer recommendations
  Future<void> sendRecommendation({required String titleId, required String recipientId, String? contextNote});
  Future<List<RecommendationEntity>> getRecommendations({String? role});
  Future<RecommendationEntity> updateRecommendationStatus({
    required String id,
    required String status,
    int? recipientActualRating,
  });

  // Leaderboard & badges
  Future<LeaderboardEntity> getSocialLeaderboard({String period});
  Future<UserBadgesEntity> getUserBadges({String? userId});
  Future<UserBadgesEntity> evaluateUserBadges();

  // Invites & referrals
  Future<InviteTokenEntity> createInviteToken();
  Future<InvitePreviewEntity> getInvitePreview(String token);
  Future<FriendshipEntity> acceptInviteToken(String token);
  Future<ReferralStatsEntity> getReferralStats();

  // Group pick rooms
  Future<PickRoomEntity> createPickRoom({
    required String title,
    required List<String> candidateTitleIds,
    int? expiresInHours,
  });
  Future<PickRoomEntity> getPickRoom(String slug);
  Future<PickVoteEntity> castPickVote({required String slug, required String titleId, String voteType});
  Future<PickRoomEntity> closePickRoom(String slug);

  // Cinema recap
  Future<RecapEntity> getUserRecap({String period, int? year});

  // Watch clubs
  Future<WatchClubEntity> createWatchClub({required String name, String? description, String? avatarUrl});
  Future<ClubDetailEntity> getWatchClub(String slug);
  Future<ClubMembershipEntity> joinWatchClub(String slug);
  Future<List<WatchClubEntity>> listMyClubs();
  Future<List<ClubActivityEntity>> getClubFeed(String slug, {int limit});

  // Monthly challenges
  Future<ChallengeEntity> createChallenge({
    required String title,
    String? description,
    String challengeType,
    String? clubId,
    required int goalCount,
    required String startsAt,
    required String endsAt,
  });
  Future<List<ChallengeEntity>> listActiveChallenges();
  Future<ChallengeDetailEntity> getChallengeDetail(String challengeId);
  Future<ChallengeParticipantEntity> joinChallenge(String challengeId);
  Future<ChallengeParticipantEntity> updateChallengeProgress({required String challengeId, int increment});

  // AI group matchmaking
  Future<GroupMatchEntity> runGroupMatchmaking({required List<String> friendIds, required String mood});
}
