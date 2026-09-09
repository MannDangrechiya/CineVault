// CineVault OS — Social Domain Entities (Part 3.1)
// Friendships, taste matching, leaderboard, badges, invites/referrals,
// pick rooms, cinema recap, watch clubs & monthly challenges.
// Mirrors apps/web/src/lib/api/{ai,personal}.ts's social-layer types —
// see services/api/routers/social.py for the canonical backend contract.

class FriendshipEntity {
  final String friendshipId;
  final String friendId;
  final String requesterId;
  final String addresseeId;
  final String? friendName;
  final String? friendUsername;
  final String? avatarUrl;
  final String status; // PENDING | ACCEPTED | BLOCKED
  final double trustScore;
  final String createdAt;

  const FriendshipEntity({
    required this.friendshipId,
    required this.friendId,
    required this.requesterId,
    required this.addresseeId,
    this.friendName,
    this.friendUsername,
    this.avatarUrl,
    required this.status,
    this.trustScore = 50.0,
    required this.createdAt,
  });

  factory FriendshipEntity.fromJson(Map<String, dynamic> json) {
    return FriendshipEntity(
      friendshipId: json['friendship_id'] ?? '',
      friendId: json['friend_id'] ?? '',
      requesterId: json['requester_id'] ?? '',
      addresseeId: json['addressee_id'] ?? '',
      friendName: json['friend_name'],
      friendUsername: json['friend_username'],
      avatarUrl: json['avatar_url'],
      status: json['status'] ?? 'PENDING',
      trustScore: (json['trust_score'] as num?)?.toDouble() ?? 50.0,
      createdAt: json['created_at'] ?? DateTime.now().toIso8601String(),
    );
  }
}

class TasteMatchEntity {
  final String friendId;
  final double compatibilityScore;

  const TasteMatchEntity({required this.friendId, required this.compatibilityScore});

  factory TasteMatchEntity.fromJson(Map<String, dynamic> json) {
    return TasteMatchEntity(
      friendId: json['friend_id'] ?? '',
      compatibilityScore: (json['compatibility_score'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class CompatibilityEntity {
  final String userId;
  final String friendId;
  final String? friendName;
  final String? friendUsername;
  final double compatibilityScore;
  final String tasteTier; // Oracle | Critic | Regular | Curious
  final List<String> sharedGenres;
  final List<String> sharedDirectors;
  final List<String> sharedFavoriteTitles;
  final String calculatedAt;

  const CompatibilityEntity({
    required this.userId,
    required this.friendId,
    this.friendName,
    this.friendUsername,
    required this.compatibilityScore,
    required this.tasteTier,
    this.sharedGenres = const [],
    this.sharedDirectors = const [],
    this.sharedFavoriteTitles = const [],
    required this.calculatedAt,
  });

  factory CompatibilityEntity.fromJson(Map<String, dynamic> json) {
    return CompatibilityEntity(
      userId: json['user_id'] ?? '',
      friendId: json['friend_id'] ?? '',
      friendName: json['friend_name'],
      friendUsername: json['friend_username'],
      compatibilityScore: (json['compatibility_score'] as num?)?.toDouble() ?? 0.0,
      tasteTier: json['taste_tier'] ?? 'Curious',
      sharedGenres: List<String>.from(json['shared_genres'] ?? const []),
      sharedDirectors: List<String>.from(json['shared_directors'] ?? const []),
      sharedFavoriteTitles: List<String>.from(json['shared_favorite_titles'] ?? const []),
      calculatedAt: json['calculated_at'] ?? DateTime.now().toIso8601String(),
    );
  }
}

class RecommendationEntity {
  final String recommendationId;
  final String senderId;
  final String? senderName;
  final String recipientId;
  final String? recipientName;
  final String titleId;
  final String? canonicalTitle;
  final String? posterUrl;
  final int? productionYear;
  final String status; // SENT | ACCEPTED | REJECTED | WATCHED | RATED
  final int? recipientActualRating;
  final String? contextNote;
  final String sentAt;
  final String updatedAt;

  const RecommendationEntity({
    required this.recommendationId,
    required this.senderId,
    this.senderName,
    required this.recipientId,
    this.recipientName,
    required this.titleId,
    this.canonicalTitle,
    this.posterUrl,
    this.productionYear,
    required this.status,
    this.recipientActualRating,
    this.contextNote,
    required this.sentAt,
    required this.updatedAt,
  });

  factory RecommendationEntity.fromJson(Map<String, dynamic> json) {
    return RecommendationEntity(
      recommendationId: json['recommendation_id'] ?? '',
      senderId: json['sender_id'] ?? '',
      senderName: json['sender_name'],
      recipientId: json['recipient_id'] ?? '',
      recipientName: json['recipient_name'],
      titleId: json['title_id'] ?? '',
      canonicalTitle: json['canonical_title'],
      posterUrl: json['poster_url'],
      productionYear: (json['production_year'] as num?)?.toInt(),
      status: json['status'] ?? 'SENT',
      recipientActualRating: (json['recipient_actual_rating'] as num?)?.toInt(),
      contextNote: json['context_note'],
      sentAt: json['sent_at'] ?? DateTime.now().toIso8601String(),
      updatedAt: json['updated_at'] ?? DateTime.now().toIso8601String(),
    );
  }
}

class LeaderboardEntryEntity {
  final String userId;
  final String? name;
  final String? username;
  final int watchCount;
  final double watchHours;
  final int rank;
  final bool isCurrentUser;

  const LeaderboardEntryEntity({
    required this.userId,
    this.name,
    this.username,
    required this.watchCount,
    required this.watchHours,
    required this.rank,
    this.isCurrentUser = false,
  });

  factory LeaderboardEntryEntity.fromJson(Map<String, dynamic> json) {
    return LeaderboardEntryEntity(
      userId: json['user_id'] ?? '',
      name: json['name'],
      username: json['username'],
      watchCount: (json['watch_count'] as num?)?.toInt() ?? 0,
      watchHours: (json['watch_hours'] as num?)?.toDouble() ?? 0.0,
      rank: (json['rank'] as num?)?.toInt() ?? 0,
      isCurrentUser: json['is_current_user'] ?? false,
    );
  }
}

class LeaderboardEntity {
  final String period; // weekly | monthly | all_time
  final List<LeaderboardEntryEntity> entries;
  final String calculatedAt;

  const LeaderboardEntity({required this.period, required this.entries, required this.calculatedAt});

  factory LeaderboardEntity.fromJson(Map<String, dynamic> json) {
    return LeaderboardEntity(
      period: json['period'] ?? 'weekly',
      entries: (json['entries'] as List? ?? const [])
          .map((e) => LeaderboardEntryEntity.fromJson(e as Map<String, dynamic>))
          .toList(),
      calculatedAt: json['calculated_at'] ?? DateTime.now().toIso8601String(),
    );
  }
}

class BadgeEntity {
  final String badgeId;
  final String slug;
  final String name;
  final String description;
  final String? iconUrl;
  final bool isEarned;
  final String? earnedAt;

  const BadgeEntity({
    required this.badgeId,
    required this.slug,
    required this.name,
    required this.description,
    this.iconUrl,
    this.isEarned = false,
    this.earnedAt,
  });

  factory BadgeEntity.fromJson(Map<String, dynamic> json) {
    return BadgeEntity(
      badgeId: json['badge_id'] ?? '',
      slug: json['slug'] ?? '',
      name: json['name'] ?? '',
      description: json['description'] ?? '',
      iconUrl: json['icon_url'],
      isEarned: json['is_earned'] ?? false,
      earnedAt: json['earned_at'],
    );
  }
}

class UserBadgesEntity {
  final String userId;
  final List<BadgeEntity> badges;
  final int totalEarned;

  const UserBadgesEntity({required this.userId, required this.badges, required this.totalEarned});

  factory UserBadgesEntity.fromJson(Map<String, dynamic> json) {
    return UserBadgesEntity(
      userId: json['user_id'] ?? '',
      badges: (json['badges'] as List? ?? const [])
          .map((e) => BadgeEntity.fromJson(e as Map<String, dynamic>))
          .toList(),
      totalEarned: (json['total_earned'] as num?)?.toInt() ?? 0,
    );
  }
}

class InviteTokenEntity {
  final String token;
  final String inviteUrl;
  final String inviterId;
  final String? inviterName;
  final String? expiresAt;
  final String createdAt;

  const InviteTokenEntity({
    required this.token,
    required this.inviteUrl,
    required this.inviterId,
    this.inviterName,
    this.expiresAt,
    required this.createdAt,
  });

  factory InviteTokenEntity.fromJson(Map<String, dynamic> json) {
    return InviteTokenEntity(
      token: json['token'] ?? '',
      inviteUrl: json['invite_url'] ?? '',
      inviterId: json['inviter_id'] ?? '',
      inviterName: json['inviter_name'],
      expiresAt: json['expires_at'],
      createdAt: json['created_at'] ?? DateTime.now().toIso8601String(),
    );
  }
}

class InvitePreviewEntity {
  final String token;
  final String inviterId;
  final String? inviterName;
  final List<String> topGenres;
  final List<String> recentWatchedTitles;
  final int totalWatchedCount;
  final bool isExpired;
  final bool isConverted;

  const InvitePreviewEntity({
    required this.token,
    required this.inviterId,
    this.inviterName,
    this.topGenres = const [],
    this.recentWatchedTitles = const [],
    this.totalWatchedCount = 0,
    this.isExpired = false,
    this.isConverted = false,
  });

  factory InvitePreviewEntity.fromJson(Map<String, dynamic> json) {
    return InvitePreviewEntity(
      token: json['token'] ?? '',
      inviterId: json['inviter_id'] ?? '',
      inviterName: json['inviter_name'],
      topGenres: List<String>.from(json['top_genres'] ?? const []),
      recentWatchedTitles: List<String>.from(json['recent_watched_titles'] ?? const []),
      totalWatchedCount: (json['total_watched_count'] as num?)?.toInt() ?? 0,
      isExpired: json['is_expired'] ?? false,
      isConverted: json['is_converted'] ?? false,
    );
  }
}

class ReferralStatsEntity {
  final String inviterId;
  final int totalInvitesSent;
  final int totalConversions;
  final int qualifiedReferrals;

  const ReferralStatsEntity({
    required this.inviterId,
    required this.totalInvitesSent,
    required this.totalConversions,
    required this.qualifiedReferrals,
  });

  factory ReferralStatsEntity.fromJson(Map<String, dynamic> json) {
    return ReferralStatsEntity(
      inviterId: json['inviter_id'] ?? '',
      totalInvitesSent: (json['total_invites_sent'] as num?)?.toInt() ?? 0,
      totalConversions: (json['total_conversions'] as num?)?.toInt() ?? 0,
      qualifiedReferrals: (json['qualified_referrals'] as num?)?.toInt() ?? 0,
    );
  }
}

class CandidateSummaryEntity {
  final String titleId;
  final String canonicalTitle;
  final int? productionYear;
  final String? posterUrl;
  final String? backdropUrl;
  final int upvotes;
  final List<String> voterNames;

  const CandidateSummaryEntity({
    required this.titleId,
    required this.canonicalTitle,
    this.productionYear,
    this.posterUrl,
    this.backdropUrl,
    this.upvotes = 0,
    this.voterNames = const [],
  });

  factory CandidateSummaryEntity.fromJson(Map<String, dynamic> json) {
    return CandidateSummaryEntity(
      titleId: json['title_id'] ?? '',
      canonicalTitle: json['canonical_title'] ?? '',
      productionYear: (json['production_year'] as num?)?.toInt(),
      posterUrl: json['poster_url'],
      backdropUrl: json['backdrop_url'],
      upvotes: (json['upvotes'] as num?)?.toInt() ?? 0,
      voterNames: List<String>.from(json['voter_names'] ?? const []),
    );
  }
}

class PickRoomEntity {
  final String roomId;
  final String hostId;
  final String? hostName;
  final String slug;
  final String title;
  final String status; // OPEN | CLOSED | RESOLVED
  final String? winningTitleId;
  final String? winningTitleName;
  final int totalVotes;
  final List<CandidateSummaryEntity> candidates;
  final String? expiresAt;
  final bool isExpired;
  final String createdAt;

  const PickRoomEntity({
    required this.roomId,
    required this.hostId,
    this.hostName,
    required this.slug,
    required this.title,
    required this.status,
    this.winningTitleId,
    this.winningTitleName,
    this.totalVotes = 0,
    this.candidates = const [],
    this.expiresAt,
    this.isExpired = false,
    required this.createdAt,
  });

  factory PickRoomEntity.fromJson(Map<String, dynamic> json) {
    return PickRoomEntity(
      roomId: json['room_id'] ?? '',
      hostId: json['host_id'] ?? '',
      hostName: json['host_name'],
      slug: json['slug'] ?? '',
      title: json['title'] ?? '',
      status: json['status'] ?? 'OPEN',
      winningTitleId: json['winning_title_id'],
      winningTitleName: json['winning_title_name'],
      totalVotes: (json['total_votes'] as num?)?.toInt() ?? 0,
      candidates: (json['candidates'] as List? ?? const [])
          .map((e) => CandidateSummaryEntity.fromJson(e as Map<String, dynamic>))
          .toList(),
      expiresAt: json['expires_at'],
      isExpired: json['is_expired'] ?? false,
      createdAt: json['created_at'] ?? DateTime.now().toIso8601String(),
    );
  }
}

class PickVoteEntity {
  final String voteId;
  final String roomId;
  final String titleId;
  final String voterName;
  final String voteType;

  const PickVoteEntity({
    required this.voteId,
    required this.roomId,
    required this.titleId,
    required this.voterName,
    required this.voteType,
  });

  factory PickVoteEntity.fromJson(Map<String, dynamic> json) {
    return PickVoteEntity(
      voteId: json['vote_id'] ?? '',
      roomId: json['room_id'] ?? '',
      titleId: json['title_id'] ?? '',
      voterName: json['voter_name'] ?? '',
      voteType: json['vote_type'] ?? 'UPVOTE',
    );
  }
}

class RecapEntity {
  final String userId;
  final String period;
  final int year;
  final int totalTitlesWatched;
  final int totalRuntimeMinutes;
  final int longestStreakDays;
  final List<Map<String, dynamic>> topGenres;
  final List<Map<String, dynamic>> topDirectors;
  final String favoriteReleaseEra;
  final double circlePercentile;
  final String cinemaArchetype;
  final String archetypeDescription;

  const RecapEntity({
    required this.userId,
    required this.period,
    required this.year,
    this.totalTitlesWatched = 0,
    this.totalRuntimeMinutes = 0,
    this.longestStreakDays = 0,
    this.topGenres = const [],
    this.topDirectors = const [],
    this.favoriteReleaseEra = '',
    this.circlePercentile = 0.0,
    this.cinemaArchetype = '',
    this.archetypeDescription = '',
  });

  factory RecapEntity.fromJson(Map<String, dynamic> json) {
    return RecapEntity(
      userId: json['user_id'] ?? '',
      period: json['period'] ?? 'yearly',
      year: (json['year'] as num?)?.toInt() ?? DateTime.now().year,
      totalTitlesWatched: (json['total_titles_watched'] as num?)?.toInt() ?? 0,
      totalRuntimeMinutes: (json['total_runtime_minutes'] as num?)?.toInt() ?? 0,
      longestStreakDays: (json['longest_streak_days'] as num?)?.toInt() ?? 0,
      topGenres: List<Map<String, dynamic>>.from(json['top_genres'] ?? const []),
      topDirectors: List<Map<String, dynamic>>.from(json['top_directors'] ?? const []),
      favoriteReleaseEra: json['favorite_release_era'] ?? '',
      circlePercentile: (json['circle_percentile'] as num?)?.toDouble() ?? 0.0,
      cinemaArchetype: json['cinema_archetype'] ?? '',
      archetypeDescription: json['archetype_description'] ?? '',
    );
  }
}

class WatchClubEntity {
  final String clubId;
  final String name;
  final String slug;
  final String createdBy;
  final String? creatorName;
  final String? avatarUrl;
  final String? description;
  final int memberCount;
  final String createdAt;

  const WatchClubEntity({
    required this.clubId,
    required this.name,
    required this.slug,
    required this.createdBy,
    this.creatorName,
    this.avatarUrl,
    this.description,
    this.memberCount = 0,
    required this.createdAt,
  });

  factory WatchClubEntity.fromJson(Map<String, dynamic> json) {
    return WatchClubEntity(
      clubId: json['club_id'] ?? '',
      name: json['name'] ?? '',
      slug: json['slug'] ?? '',
      createdBy: json['created_by'] ?? '',
      creatorName: json['creator_name'],
      avatarUrl: json['avatar_url'],
      description: json['description'],
      memberCount: (json['member_count'] as num?)?.toInt() ?? 0,
      createdAt: json['created_at'] ?? DateTime.now().toIso8601String(),
    );
  }
}

class ClubMembershipEntity {
  final String clubId;
  final String userId;
  final String? userName;
  final String role;
  final String joinedAt;

  const ClubMembershipEntity({
    required this.clubId,
    required this.userId,
    this.userName,
    required this.role,
    required this.joinedAt,
  });

  factory ClubMembershipEntity.fromJson(Map<String, dynamic> json) {
    return ClubMembershipEntity(
      clubId: json['club_id'] ?? '',
      userId: json['user_id'] ?? '',
      userName: json['user_name'],
      role: json['role'] ?? 'member',
      joinedAt: json['joined_at'] ?? DateTime.now().toIso8601String(),
    );
  }
}

class ClubDetailEntity {
  final WatchClubEntity club;
  final List<ClubMembershipEntity> members;

  const ClubDetailEntity({required this.club, required this.members});

  factory ClubDetailEntity.fromJson(Map<String, dynamic> json) {
    return ClubDetailEntity(
      club: WatchClubEntity.fromJson(json['club'] as Map<String, dynamic>),
      members: (json['members'] as List? ?? const [])
          .map((e) => ClubMembershipEntity.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

class ClubActivityEntity {
  final String activityId;
  final String clubId;
  final String userId;
  final String? userName;
  final String activityType;
  final String? referenceId;
  final String createdAt;

  const ClubActivityEntity({
    required this.activityId,
    required this.clubId,
    required this.userId,
    this.userName,
    required this.activityType,
    this.referenceId,
    required this.createdAt,
  });

  factory ClubActivityEntity.fromJson(Map<String, dynamic> json) {
    return ClubActivityEntity(
      activityId: json['activity_id'] ?? '',
      clubId: json['club_id'] ?? '',
      userId: json['user_id'] ?? '',
      userName: json['user_name'],
      activityType: json['activity_type'] ?? '',
      referenceId: json['reference_id'],
      createdAt: json['created_at'] ?? DateTime.now().toIso8601String(),
    );
  }
}

class ChallengeEntity {
  final String challengeId;
  final String title;
  final String? description;
  final String challengeType;
  final String? clubId;
  final int goalCount;
  final String startsAt;
  final String endsAt;
  final int participantCount;
  final int? myProgress;
  final bool myCompleted;

  const ChallengeEntity({
    required this.challengeId,
    required this.title,
    this.description,
    required this.challengeType,
    this.clubId,
    required this.goalCount,
    required this.startsAt,
    required this.endsAt,
    this.participantCount = 0,
    this.myProgress,
    this.myCompleted = false,
  });

  factory ChallengeEntity.fromJson(Map<String, dynamic> json) {
    return ChallengeEntity(
      challengeId: json['challenge_id'] ?? '',
      title: json['title'] ?? '',
      description: json['description'],
      challengeType: json['challenge_type'] ?? '',
      clubId: json['club_id'],
      goalCount: (json['goal_count'] as num?)?.toInt() ?? 0,
      startsAt: json['starts_at'] ?? '',
      endsAt: json['ends_at'] ?? '',
      participantCount: (json['participant_count'] as num?)?.toInt() ?? 0,
      myProgress: (json['my_progress'] as num?)?.toInt(),
      myCompleted: json['my_completed'] ?? false,
    );
  }
}

class ChallengeParticipantEntity {
  final String challengeId;
  final String userId;
  final String? userName;
  final int progress;
  final bool completed;
  final String joinedAt;

  const ChallengeParticipantEntity({
    required this.challengeId,
    required this.userId,
    this.userName,
    required this.progress,
    this.completed = false,
    required this.joinedAt,
  });

  factory ChallengeParticipantEntity.fromJson(Map<String, dynamic> json) {
    return ChallengeParticipantEntity(
      challengeId: json['challenge_id'] ?? '',
      userId: json['user_id'] ?? '',
      userName: json['user_name'],
      progress: (json['progress'] as num?)?.toInt() ?? 0,
      completed: json['completed'] ?? false,
      joinedAt: json['joined_at'] ?? DateTime.now().toIso8601String(),
    );
  }
}

class ChallengeDetailEntity {
  final ChallengeEntity challenge;
  final List<ChallengeParticipantEntity> participants;

  const ChallengeDetailEntity({required this.challenge, required this.participants});

  factory ChallengeDetailEntity.fromJson(Map<String, dynamic> json) {
    return ChallengeDetailEntity(
      challenge: ChallengeEntity.fromJson(json['challenge'] as Map<String, dynamic>),
      participants: (json['participants'] as List? ?? const [])
          .map((e) => ChallengeParticipantEntity.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

class GroupMatchEntity {
  final String status;
  final String mood;
  final int groupSize;
  final List<String> groupMemberIds;
  final List<String> recommendedTitles;
  final String aiRecommendation;

  const GroupMatchEntity({
    required this.status,
    required this.mood,
    required this.groupSize,
    this.groupMemberIds = const [],
    this.recommendedTitles = const [],
    required this.aiRecommendation,
  });

  factory GroupMatchEntity.fromJson(Map<String, dynamic> json) {
    return GroupMatchEntity(
      status: json['status'] ?? '',
      mood: json['mood'] ?? '',
      groupSize: (json['group_size'] as num?)?.toInt() ?? 0,
      groupMemberIds: List<String>.from(json['group_member_ids'] ?? const []),
      recommendedTitles: List<String>.from(json['recommended_titles'] ?? const []),
      aiRecommendation: json['ai_recommendation'] ?? '',
    );
  }
}
