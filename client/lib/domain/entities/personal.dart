// CineVault OS — Personal Domain Entities (8.2, CAT-2)
// Append-only watch events, user title states, ratings, notes & reviews

class WatchEventEntity {
  final String watchEventId;
  final String titleId;
  final String eventTimestamp;
  final String watchMode; // THEATER, STREAMING, HOME_MEDIA
  final double? ratingValue;
  final String? notes;

  const WatchEventEntity({
    required this.watchEventId,
    required this.titleId,
    required this.eventTimestamp,
    required this.watchMode,
    this.ratingValue,
    this.notes,
  });

  factory WatchEventEntity.fromJson(Map<String, dynamic> json) {
    return WatchEventEntity(
      watchEventId: json['watch_event_id'] ?? json['id'] ?? '',
      titleId: json['title_id'] ?? '',
      eventTimestamp: json['event_timestamp'] ?? json['timestamp'] ?? DateTime.now().toIso8601String(),
      watchMode: json['watch_mode'] ?? 'STREAMING',
      ratingValue: json['rating_value'] != null ? (json['rating_value'] as num).toDouble() : null,
      notes: json['notes'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'watch_event_id': watchEventId,
      'title_id': titleId,
      'event_timestamp': eventTimestamp,
      'watch_mode': watchMode,
      'rating_value': ratingValue,
      'notes': notes,
    };
  }
}

class UserRatingEntity {
  final String ratingId;
  final String titleId;
  final double ratingValue; // 0.5 - 10.0
  final String? reviewText;
  final String updatedAt;

  const UserRatingEntity({
    required this.ratingId,
    required this.titleId,
    required this.ratingValue,
    this.reviewText,
    required this.updatedAt,
  });

  factory UserRatingEntity.fromJson(Map<String, dynamic> json) {
    return UserRatingEntity(
      ratingId: json['rating_id'] ?? '',
      titleId: json['title_id'] ?? '',
      ratingValue: (json['rating_value'] as num).toDouble(),
      reviewText: json['review_text'],
      updatedAt: json['updated_at'] ?? DateTime.now().toIso8601String(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'rating_id': ratingId,
      'title_id': titleId,
      'rating_value': ratingValue,
      'review_text': reviewText,
      'updated_at': updatedAt,
    };
  }
}

class UserNoteEntity {
  final String noteId;
  final String titleId;
  final String noteContent;
  final bool isPrivate;
  final String updatedAt;

  const UserNoteEntity({
    required this.noteId,
    required this.titleId,
    required this.noteContent,
    required this.isPrivate,
    required this.updatedAt,
  });

  factory UserNoteEntity.fromJson(Map<String, dynamic> json) {
    return UserNoteEntity(
      noteId: json['note_id'] ?? '',
      titleId: json['title_id'] ?? '',
      noteContent: json['note_content'] ?? '',
      isPrivate: json['is_private'] ?? true,
      updatedAt: json['updated_at'] ?? DateTime.now().toIso8601String(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'note_id': noteId,
      'title_id': titleId,
      'note_content': noteContent,
      'is_private': isPrivate,
      'updated_at': updatedAt,
    };
  }
}
