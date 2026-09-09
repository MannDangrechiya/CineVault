// CineVault OS — Social Remote Datasource (Part 3.1)
// All /social/* endpoint calls, plus /ai/group-matchmaking. Ports
// apps/web/src/lib/api/{ai,personal}.ts's social-layer client 1:1 —
// see services/api/routers/social.py for the backend contract.

import '../../core/config/api_config.dart';
import '../../core/network/api_client.dart';
import '../../domain/entities/social.dart';

class SocialRemoteDatasource {
  final ApiClient _apiClient;

  SocialRemoteDatasource({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  // ── Friendships ────────────────────────────────────────────────────────

  Future<List<FriendshipEntity>> getFriendships() async {
    final response = await _apiClient.dio.get(ApiConfig.friendshipsEndpoint);
    final List data = response.data ?? [];
    return data.map((json) => FriendshipEntity.fromJson(json)).toList();
  }

  Future<FriendshipEntity> sendFriendRequest(String addresseeId) async {
    final response = await _apiClient.dio.post(
      ApiConfig.friendshipsEndpoint,
      data: {'addressee_id': addresseeId},
    );
    return FriendshipEntity.fromJson(response.data);
  }

  Future<FriendshipEntity> updateFriendshipStatus({
    required String friendshipId,
    required String status, // 'ACCEPTED' | 'BLOCKED'
  }) async {
    final response = await _apiClient.dio.patch(
      '${ApiConfig.friendshipsEndpoint}/$friendshipId',
      data: {'status': status},
    );
    return FriendshipEntity.fromJson(response.data);
  }

  Future<void> deleteFriendship(String friendshipId) async {
    await _apiClient.dio.delete('${ApiConfig.friendshipsEndpoint}/$friendshipId');
  }

  Future<CompatibilityEntity> getFriendCompatibility(String friendId) async {
    final response = await _apiClient.dio.get(
      '${ApiConfig.friendshipsEndpoint}/$friendId/compatibility',
    );
    return CompatibilityEntity.fromJson(response.data);
  }

  Future<List<TasteMatchEntity>> getTasteMatches({int limit = 50}) async {
    final response = await _apiClient.dio.get(
      ApiConfig.tasteMatchesEndpoint,
      queryParameters: {'limit': limit},
    );
    final List data = response.data ?? [];
    return data.map((json) => TasteMatchEntity.fromJson(json)).toList();
  }

  // ── Peer Recommendations ──────────────────────────────────────────────

  Future<void> sendRecommendation({
    required String titleId,
    required String recipientId,
    String? contextNote,
  }) async {
    await _apiClient.dio.post(
      ApiConfig.socialRecommendationsEndpoint,
      data: {
        'title_id': titleId,
        'recipient_id': recipientId,
        if (contextNote != null) 'context_note': contextNote,
      },
    );
  }

  Future<List<RecommendationEntity>> getRecommendations({String? role}) async {
    final response = await _apiClient.dio.get(
      ApiConfig.socialRecommendationsEndpoint,
      queryParameters: role != null ? {'role': role} : null,
    );
    final List data = response.data ?? [];
    return data.map((json) => RecommendationEntity.fromJson(json)).toList();
  }

  Future<RecommendationEntity> updateRecommendationStatus({
    required String id,
    required String status, // ACCEPTED | REJECTED | WATCHED | RATED
    int? recipientActualRating,
  }) async {
    final response = await _apiClient.dio.patch(
      '${ApiConfig.socialRecommendationsEndpoint}/$id',
      data: {
        'status': status,
        if (recipientActualRating != null) 'recipient_actual_rating': recipientActualRating,
      },
    );
    return RecommendationEntity.fromJson(response.data);
  }

  // ── Leaderboard & Badges ──────────────────────────────────────────────

  Future<LeaderboardEntity> getSocialLeaderboard({String period = 'weekly'}) async {
    final response = await _apiClient.dio.get(
      ApiConfig.leaderboardEndpoint,
      queryParameters: {'period': period},
    );
    return LeaderboardEntity.fromJson(response.data);
  }

  Future<UserBadgesEntity> getUserBadges({String? userId}) async {
    final path = userId != null ? '${ApiConfig.badgesEndpoint}/$userId' : ApiConfig.badgesEndpoint;
    final response = await _apiClient.dio.get(path);
    return UserBadgesEntity.fromJson(response.data);
  }

  Future<UserBadgesEntity> evaluateUserBadges() async {
    final response = await _apiClient.dio.post('${ApiConfig.badgesEndpoint}/evaluate');
    return UserBadgesEntity.fromJson(response.data);
  }

  // ── Invites & Referrals ───────────────────────────────────────────────

  Future<InviteTokenEntity> createInviteToken() async {
    final response = await _apiClient.dio.post(ApiConfig.invitesEndpoint);
    return InviteTokenEntity.fromJson(response.data);
  }

  Future<InvitePreviewEntity> getInvitePreview(String token) async {
    final response = await _apiClient.dio.get('${ApiConfig.invitesEndpoint}/$token/preview');
    return InvitePreviewEntity.fromJson(response.data);
  }

  Future<FriendshipEntity> acceptInviteToken(String token) async {
    final response = await _apiClient.dio.post('${ApiConfig.invitesEndpoint}/$token/accept');
    return FriendshipEntity.fromJson(response.data);
  }

  Future<ReferralStatsEntity> getReferralStats() async {
    final response = await _apiClient.dio.get(ApiConfig.referralsEndpoint);
    return ReferralStatsEntity.fromJson(response.data);
  }

  // ── Group Pick Rooms ───────────────────────────────────────────────────

  Future<PickRoomEntity> createPickRoom({
    required String title,
    required List<String> candidateTitleIds,
    int? expiresInHours,
  }) async {
    final response = await _apiClient.dio.post(
      ApiConfig.pickRoomsEndpoint,
      data: {
        'title': title,
        'candidate_title_ids': candidateTitleIds,
        if (expiresInHours != null) 'expires_in_hours': expiresInHours,
      },
    );
    return PickRoomEntity.fromJson(response.data);
  }

  Future<PickRoomEntity> getPickRoom(String slug) async {
    final response = await _apiClient.dio.get('${ApiConfig.pickRoomsEndpoint}/$slug');
    return PickRoomEntity.fromJson(response.data);
  }

  Future<PickVoteEntity> castPickVote({
    required String slug,
    required String titleId,
    String voteType = 'UPVOTE',
  }) async {
    final response = await _apiClient.dio.post(
      '${ApiConfig.pickRoomsEndpoint}/$slug/vote',
      data: {'title_id': titleId, 'vote_type': voteType},
    );
    return PickVoteEntity.fromJson(response.data);
  }

  Future<PickRoomEntity> closePickRoom(String slug) async {
    final response = await _apiClient.dio.post('${ApiConfig.pickRoomsEndpoint}/$slug/close');
    return PickRoomEntity.fromJson(response.data);
  }

  // ── Cinema Recap ───────────────────────────────────────────────────────

  Future<RecapEntity> getUserRecap({String period = 'yearly', int? year}) async {
    final response = await _apiClient.dio.get(
      ApiConfig.recapEndpoint,
      queryParameters: {'period': period, if (year != null) 'year': year},
    );
    return RecapEntity.fromJson(response.data);
  }

  // ── Watch Clubs ────────────────────────────────────────────────────────

  Future<WatchClubEntity> createWatchClub({
    required String name,
    String? description,
    String? avatarUrl,
  }) async {
    final response = await _apiClient.dio.post(
      ApiConfig.clubsEndpoint,
      data: {
        'name': name,
        if (description != null) 'description': description,
        if (avatarUrl != null) 'avatar_url': avatarUrl,
      },
    );
    return WatchClubEntity.fromJson(response.data);
  }

  Future<ClubDetailEntity> getWatchClub(String slug) async {
    final response = await _apiClient.dio.get('${ApiConfig.clubsEndpoint}/$slug');
    return ClubDetailEntity.fromJson(response.data);
  }

  Future<ClubMembershipEntity> joinWatchClub(String slug) async {
    final response = await _apiClient.dio.post('${ApiConfig.clubsEndpoint}/$slug/join');
    return ClubMembershipEntity.fromJson(response.data);
  }

  Future<List<WatchClubEntity>> listMyClubs() async {
    final response = await _apiClient.dio.get(ApiConfig.clubsEndpoint);
    final List data = response.data ?? [];
    return data.map((json) => WatchClubEntity.fromJson(json)).toList();
  }

  Future<List<ClubActivityEntity>> getClubFeed(String slug, {int limit = 20}) async {
    final response = await _apiClient.dio.get(
      '${ApiConfig.clubsEndpoint}/$slug/feed',
      queryParameters: {'limit': limit},
    );
    final List data = response.data ?? [];
    return data.map((json) => ClubActivityEntity.fromJson(json)).toList();
  }

  // ── Monthly Challenges ─────────────────────────────────────────────────

  Future<ChallengeEntity> createChallenge({
    required String title,
    String? description,
    String challengeType = 'personal',
    String? clubId,
    required int goalCount,
    required String startsAt,
    required String endsAt,
  }) async {
    final response = await _apiClient.dio.post(
      ApiConfig.challengesEndpoint,
      data: {
        'title': title,
        if (description != null) 'description': description,
        'challenge_type': challengeType,
        if (clubId != null) 'club_id': clubId,
        'goal_count': goalCount,
        'starts_at': startsAt,
        'ends_at': endsAt,
      },
    );
    return ChallengeEntity.fromJson(response.data);
  }

  Future<List<ChallengeEntity>> listActiveChallenges() async {
    final response = await _apiClient.dio.get(ApiConfig.challengesEndpoint);
    final List data = response.data ?? [];
    return data.map((json) => ChallengeEntity.fromJson(json)).toList();
  }

  Future<ChallengeDetailEntity> getChallengeDetail(String challengeId) async {
    final response = await _apiClient.dio.get('${ApiConfig.challengesEndpoint}/$challengeId');
    return ChallengeDetailEntity.fromJson(response.data);
  }

  Future<ChallengeParticipantEntity> joinChallenge(String challengeId) async {
    final response = await _apiClient.dio.post('${ApiConfig.challengesEndpoint}/$challengeId/join');
    return ChallengeParticipantEntity.fromJson(response.data);
  }

  Future<ChallengeParticipantEntity> updateChallengeProgress({
    required String challengeId,
    int increment = 1,
  }) async {
    final response = await _apiClient.dio.post(
      '${ApiConfig.challengesEndpoint}/$challengeId/progress',
      queryParameters: {'increment': increment},
    );
    return ChallengeParticipantEntity.fromJson(response.data);
  }

  // ── AI Group Matchmaking ──────────────────────────────────────────────

  Future<GroupMatchEntity> runGroupMatchmaking({
    required List<String> friendIds,
    required String mood,
  }) async {
    final response = await _apiClient.dio.post(
      ApiConfig.groupMatchmakingEndpoint,
      data: {'friend_ids': friendIds, 'mood': mood},
    );
    return GroupMatchEntity.fromJson(response.data);
  }
}
