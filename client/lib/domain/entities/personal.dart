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
