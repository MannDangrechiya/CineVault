// CineVault OS — Personal Domain Entities (8.2, CAT-2)
// Append-only watch events, user title states, ratings, notes & reviews

class WatchEventEntity {
  final String watchEventId;
  final String titleId;
  final String? userId;
  final String? editionId;
  final String watchedAt;
  final double progressPercentage;
  final String? createdAt;

  const WatchEventEntity({
    required this.watchEventId,
    required this.titleId,
    this.userId,
    this.editionId,
    required this.watchedAt,
    this.progressPercentage = 100.0,
    this.createdAt,
  });

  factory WatchEventEntity.fromJson(Map<String, dynamic> json) {
    return WatchEventEntity(
      watchEventId: json['id'] ?? json['watch_event_id'] ?? '',
      titleId: json['title_id'] ?? '',
      userId: json['user_id'],
      editionId: json['edition_id'],
      watchedAt: json['watched_at'] ?? json['event_timestamp'] ?? json['timestamp'] ?? DateTime.now().toIso8601String(),
      progressPercentage: (json['progress_percentage'] as num?)?.toDouble() ?? 100.0,
      createdAt: json['created_at'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'title_id': titleId,
      'watched_at': watchedAt,
      'progress_percentage': progressPercentage,
      if (editionId != null) 'edition_id': editionId,
    };
  }
}

class UserRatingEntity {
  final String ratingId;
  final String titleId;
  final int ratingValue; // 1 - 10 (int per backend RatingResponse)
  final String updatedAt;

  const UserRatingEntity({
    required this.ratingId,
    required this.titleId,
    required this.ratingValue,
    required this.updatedAt,
  });

  factory UserRatingEntity.fromJson(Map<String, dynamic> json) {
    return UserRatingEntity(
      ratingId: json['id'] ?? json['rating_id'] ?? '',
      titleId: json['title_id'] ?? '',
      ratingValue: (json['rating_value'] as num).toInt(),
      updatedAt: json['updated_at'] ?? DateTime.now().toIso8601String(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'title_id': titleId,
      'rating_value': ratingValue,
    };
  }
}

class UserNoteEntity {
  final String noteId;
  final String titleId;
  final String noteText;
  final String updatedAt;

  const UserNoteEntity({
    required this.noteId,
    required this.titleId,
    required this.noteText,
    required this.updatedAt,
  });

  factory UserNoteEntity.fromJson(Map<String, dynamic> json) {
    return UserNoteEntity(
      noteId: json['id'] ?? json['note_id'] ?? '',
      titleId: json['title_id'] ?? '',
      noteText: json['note_text'] ?? json['note_content'] ?? '',
      updatedAt: json['updated_at'] ?? DateTime.now().toIso8601String(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'title_id': titleId,
      'note_text': noteText,
    };
  }
}

class ReviewEntity {
  final String reviewId;
  final String titleId;
  final String? reviewTitle;
  final String reviewText;
  final bool isPublic;
  final String createdAt;

  const ReviewEntity({
    required this.reviewId,
    required this.titleId,
    this.reviewTitle,
    required this.reviewText,
    this.isPublic = true,
    required this.createdAt,
  });

  factory ReviewEntity.fromJson(Map<String, dynamic> json) {
    return ReviewEntity(
      reviewId: json['id'] ?? json['review_id'] ?? '',
      titleId: json['title_id'] ?? '',
      reviewTitle: json['review_title'],
      reviewText: json['review_text'] ?? '',
      isPublic: json['is_public'] ?? true,
      createdAt: json['created_at'] ?? DateTime.now().toIso8601String(),
    );
  }
}

class WatchlistItemEntity {
  final String id;
  final String titleId;
  final String canonicalTitle;
  final int? productionYear;
  final String contentType;
  final String? posterUrl;
  final String addedAt;

  const WatchlistItemEntity({
    required this.id,
    required this.titleId,
    required this.canonicalTitle,
    this.productionYear,
    required this.contentType,
    this.posterUrl,
    required this.addedAt,
  });

  factory WatchlistItemEntity.fromJson(Map<String, dynamic> json) {
    return WatchlistItemEntity(
      id: json['id'] ?? '',
      titleId: json['title_id'] ?? '',
      canonicalTitle: json['canonical_title'] ?? '',
      productionYear: (json['production_year'] as num?)?.toInt(),
      contentType: json['content_type'] ?? '',
      posterUrl: json['poster_url'],
      addedAt: json['added_at'] ?? DateTime.now().toIso8601String(),
    );
  }
}

class HistoryItemEntity {
  final String id;
  final String titleId;
  final String canonicalTitle;
  final int? productionYear;
  final String contentType;
  final String? posterUrl;
  final String watchedAt;
  final int? ratingValue;
  final double progressPercentage;

  const HistoryItemEntity({
    required this.id,
    required this.titleId,
    required this.canonicalTitle,
    this.productionYear,
    required this.contentType,
    this.posterUrl,
    required this.watchedAt,
    this.ratingValue,
    this.progressPercentage = 100.0,
  });

  factory HistoryItemEntity.fromJson(Map<String, dynamic> json) {
    return HistoryItemEntity(
      id: json['id'] ?? '',
      titleId: json['title_id'] ?? '',
      canonicalTitle: json['canonical_title'] ?? '',
      productionYear: (json['production_year'] as num?)?.toInt(),
      contentType: json['content_type'] ?? '',
      posterUrl: json['poster_url'],
      watchedAt: json['watched_at'] ?? DateTime.now().toIso8601String(),
      ratingValue: (json['rating_value'] as num?)?.toInt(),
      progressPercentage: (json['progress_percentage'] as num?)?.toDouble() ?? 100.0,
    );
  }
}

class UserStreakEntity {
  final int currentStreak;
  final int longestStreak;
  final String? lastWatchDate;

  const UserStreakEntity({
    this.currentStreak = 0,
    this.longestStreak = 0,
    this.lastWatchDate,
  });

  factory UserStreakEntity.fromJson(Map<String, dynamic> json) {
    return UserStreakEntity(
      currentStreak: (json['current_streak'] as num?)?.toInt() ?? 0,
      longestStreak: (json['longest_streak'] as num?)?.toInt() ?? 0,
      lastWatchDate: json['last_watch_date'],
    );
  }
}

class PersonalAnalyticsEntity {
  final double totalWatchHours;
  final int watchedCount;
  final int watchStreakDays;
  final double tasteMatchScore;
  final int moviesWatched;
  final int seriesCompleted;
  final int pendingRecommendationsCount;
  final List<Map<String, dynamic>> topGenres;

  const PersonalAnalyticsEntity({
    this.totalWatchHours = 0,
    this.watchedCount = 0,
    this.watchStreakDays = 0,
    this.tasteMatchScore = 0,
    this.moviesWatched = 0,
    this.seriesCompleted = 0,
    this.pendingRecommendationsCount = 0,
    this.topGenres = const [],
  });

  factory PersonalAnalyticsEntity.fromJson(Map<String, dynamic> json) {
    return PersonalAnalyticsEntity(
      totalWatchHours: (json['total_watch_hours'] as num?)?.toDouble() ?? 0,
      watchedCount: (json['watched_count'] as num?)?.toInt() ?? 0,
      watchStreakDays: (json['watch_streak_days'] as num?)?.toInt() ?? 0,
      tasteMatchScore: (json['taste_match_score'] as num?)?.toDouble() ?? 0,
      moviesWatched: (json['movies_watched'] as num?)?.toInt() ?? 0,
      seriesCompleted: (json['series_completed'] as num?)?.toInt() ?? 0,
      pendingRecommendationsCount: (json['pending_recommendations_count'] as num?)?.toInt() ?? 0,
      topGenres: List<Map<String, dynamic>>.from(json['top_genres'] ?? const []),
    );
  }
}

class UserTitleStateEntity {
  final String titleId;
  final String derivedStatus;
  final String? manualStatusOverride;
  final bool isFavorite;
  final String? preferredEditionId;
  final String updatedAt;

  const UserTitleStateEntity({
    required this.titleId,
    required this.derivedStatus,
    this.manualStatusOverride,
    this.isFavorite = false,
    this.preferredEditionId,
    required this.updatedAt,
  });

  factory UserTitleStateEntity.fromJson(Map<String, dynamic> json) {
    return UserTitleStateEntity(
      titleId: json['title_id'] ?? '',
      derivedStatus: json['derived_status'] ?? 'UNWATCHED',
      manualStatusOverride: json['manual_status_override'],
      isFavorite: json['is_favorite'] ?? false,
      preferredEditionId: json['preferred_edition_id'],
      updatedAt: json['updated_at'] ?? DateTime.now().toIso8601String(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'title_id': titleId,
      'derived_status': derivedStatus,
      if (manualStatusOverride != null) 'manual_status_override': manualStatusOverride,
      'is_favorite': isFavorite,
      if (preferredEditionId != null) 'preferred_edition_id': preferredEditionId,
    };
  }
}

