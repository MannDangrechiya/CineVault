// CineVault OS — Social Repository Implementation (Part 3.1)

import '../../domain/entities/social.dart';
import '../../domain/repositories/social_repository.dart';
import '../remote/social_remote_datasource.dart';

class SocialRepositoryImpl implements SocialRepository {
  final SocialRemoteDatasource _remoteDatasource;

  SocialRepositoryImpl({SocialRemoteDatasource? remoteDatasource})
      : _remoteDatasource = remoteDatasource ?? SocialRemoteDatasource();

  @override
  Future<List<FriendshipEntity>> getFriendships() => _remoteDatasource.getFriendships();

  @override
  Future<FriendshipEntity> sendFriendRequest(String addresseeId) =>
      _remoteDatasource.sendFriendRequest(addresseeId);

  @override
  Future<FriendshipEntity> updateFriendshipStatus({required String friendshipId, required String status}) =>
      _remoteDatasource.updateFriendshipStatus(friendshipId: friendshipId, status: status);

  @override
  Future<void> deleteFriendship(String friendshipId) => _remoteDatasource.deleteFriendship(friendshipId);

  @override
  Future<CompatibilityEntity> getFriendCompatibility(String friendId) =>
      _remoteDatasource.getFriendCompatibility(friendId);

  @override
  Future<List<TasteMatchEntity>> getTasteMatches({int limit = 50}) =>
      _remoteDatasource.getTasteMatches(limit: limit);

  @override
  Future<void> sendRecommendation({required String titleId, required String recipientId, String? contextNote}) =>
      _remoteDatasource.sendRecommendation(titleId: titleId, recipientId: recipientId, contextNote: contextNote);

  @override
  Future<List<RecommendationEntity>> getRecommendations({String? role}) =>
      _remoteDatasource.getRecommendations(role: role);

  @override
  Future<RecommendationEntity> updateRecommendationStatus({
    required String id,
    required String status,
    int? recipientActualRating,
  }) =>
      _remoteDatasource.updateRecommendationStatus(
        id: id,
        status: status,
        recipientActualRating: recipientActualRating,
      );

  @override
  Future<LeaderboardEntity> getSocialLeaderboard({String period = 'weekly'}) =>
      _remoteDatasource.getSocialLeaderboard(period: period);

  @override
  Future<UserBadgesEntity> getUserBadges({String? userId}) => _remoteDatasource.getUserBadges(userId: userId);

  @override
  Future<UserBadgesEntity> evaluateUserBadges() => _remoteDatasource.evaluateUserBadges();

  @override
  Future<InviteTokenEntity> createInviteToken() => _remoteDatasource.createInviteToken();

  @override
  Future<InvitePreviewEntity> getInvitePreview(String token) => _remoteDatasource.getInvitePreview(token);

  @override
  Future<FriendshipEntity> acceptInviteToken(String token) => _remoteDatasource.acceptInviteToken(token);

  @override
  Future<ReferralStatsEntity> getReferralStats() => _remoteDatasource.getReferralStats();

  @override
  Future<PickRoomEntity> createPickRoom({
    required String title,
    required List<String> candidateTitleIds,
    int? expiresInHours,
  }) =>
      _remoteDatasource.createPickRoom(
        title: title,
        candidateTitleIds: candidateTitleIds,
        expiresInHours: expiresInHours,
      );

  @override
  Future<PickRoomEntity> getPickRoom(String slug) => _remoteDatasource.getPickRoom(slug);

  @override
  Future<PickVoteEntity> castPickVote({required String slug, required String titleId, String voteType = 'UPVOTE'}) =>
      _remoteDatasource.castPickVote(slug: slug, titleId: titleId, voteType: voteType);

  @override
  Future<PickRoomEntity> closePickRoom(String slug) => _remoteDatasource.closePickRoom(slug);

  @override
  Future<RecapEntity> getUserRecap({String period = 'yearly', int? year}) =>
      _remoteDatasource.getUserRecap(period: period, year: year);

  @override
  Future<WatchClubEntity> createWatchClub({required String name, String? description, String? avatarUrl}) =>
      _remoteDatasource.createWatchClub(name: name, description: description, avatarUrl: avatarUrl);

  @override
  Future<ClubDetailEntity> getWatchClub(String slug) => _remoteDatasource.getWatchClub(slug);

  @override
  Future<ClubMembershipEntity> joinWatchClub(String slug) => _remoteDatasource.joinWatchClub(slug);

  @override
  Future<List<WatchClubEntity>> listMyClubs() => _remoteDatasource.listMyClubs();

  @override
  Future<List<ClubActivityEntity>> getClubFeed(String slug, {int limit = 20}) =>
      _remoteDatasource.getClubFeed(slug, limit: limit);

  @override
  Future<ChallengeEntity> createChallenge({
    required String title,
    String? description,
    String challengeType = 'personal',
    String? clubId,
    required int goalCount,
    required String startsAt,
    required String endsAt,
  }) =>
      _remoteDatasource.createChallenge(
        title: title,
        description: description,
        challengeType: challengeType,
        clubId: clubId,
        goalCount: goalCount,
        startsAt: startsAt,
        endsAt: endsAt,
      );

  @override
  Future<List<ChallengeEntity>> listActiveChallenges() => _remoteDatasource.listActiveChallenges();

  @override
  Future<ChallengeDetailEntity> getChallengeDetail(String challengeId) =>
      _remoteDatasource.getChallengeDetail(challengeId);

  @override
  Future<ChallengeParticipantEntity> joinChallenge(String challengeId) =>
      _remoteDatasource.joinChallenge(challengeId);

  @override
  Future<ChallengeParticipantEntity> updateChallengeProgress({required String challengeId, int increment = 1}) =>
      _remoteDatasource.updateChallengeProgress(challengeId: challengeId, increment: increment);

  @override
  Future<GroupMatchEntity> runGroupMatchmaking({required List<String> friendIds, required String mood}) =>
      _remoteDatasource.runGroupMatchmaking(friendIds: friendIds, mood: mood);
}
