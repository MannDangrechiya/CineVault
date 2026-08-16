// CineVault OS — Personal Offline Repository (Phase 18 / ADR-004)
// Implements offline-first personal library data persistence in Drift SQLite and outbox mutation queueing

import 'dart:convert';
import 'package:drift/drift.dart';
import '../../core/utils/uuid_util.dart';
import '../../domain/entities/personal.dart';
import '../local/app_database.dart';

class PersonalOfflineRepository {
  final AppDatabase _db;

  PersonalOfflineRepository(this._db);

  // --------------------------------------------------------------------------
  // Watch History & Progress (Offline-First)
  // --------------------------------------------------------------------------

  Future<WatchEventEntity> recordOfflineWatchEvent({
    required String titleId,
    String? notes,
    double progressPercentage = 100.0,
    String? customEventId,
  }) async {
    final eventId = customEventId ?? UuidUtil.generateMutationId();
    final nowIso = DateTime.now().toUtc().toIso8601String();

    // 1. Write to local Drift SQLite table
    await _db.upsertOfflineWatchEvent(
      OfflineWatchEventsCompanion.insert(
        watchEventId: eventId,
        titleId: titleId,
        watchedAt: nowIso,
        progressPercentage: Value(progressPercentage),
        notes: Value(notes),
        isTombstoned: const Value(false),
      ),
    );

    // 2. Queue into durable Outbox for background/online sync
    final mutationId = UuidUtil.generateMutationId();
    final payload = {
      'watch_event_id': eventId,
      'title_id': titleId,
      'watched_at': nowIso,
      'progress_percentage': progressPercentage,
      if (notes != null) 'notes': notes,
    };

    await _db.insertMutation(
      OutboxMutationsCompanion.insert(
        mutationId: mutationId,
        mutationType: 'CREATE_WATCH_EVENT',
        clientTimestamp: nowIso,
        payloadJson: jsonEncode(payload),
        status: const Value('PENDING'),
      ),
    );

    return WatchEventEntity(
      watchEventId: eventId,
      titleId: titleId,
      watchedAt: nowIso,
      progressPercentage: progressPercentage,
      createdAt: nowIso,
    );
  }

  Future<List<WatchEventEntity>> getOfflineWatchHistory() async {
    final rows = await _db.getOfflineWatchEvents();
    return rows.map((row) {
      return WatchEventEntity(
        watchEventId: row.watchEventId,
        titleId: row.titleId,
        watchedAt: row.watchedAt,
        progressPercentage: row.progressPercentage,
      );
    }).toList();
  }

  // --------------------------------------------------------------------------
  // Personal Ratings (Offline-First)
  // --------------------------------------------------------------------------

  Future<UserRatingEntity> setOfflineRating({
    required String titleId,
    required int ratingValue,
    String? customRatingId,
  }) async {
    final ratingId = customRatingId ?? UuidUtil.generateMutationId();
    final nowIso = DateTime.now().toUtc().toIso8601String();

    await _db.upsertOfflineRating(
      OfflineRatingsCompanion.insert(
        ratingId: ratingId,
        titleId: titleId,
        ratingValue: ratingValue,
        ratedAt: nowIso,
      ),
    );

    final mutationId = UuidUtil.generateMutationId();
    final payload = {
      'title_id': titleId,
      'rating_value': ratingValue,
      'rated_at': nowIso,
    };

    await _db.insertMutation(
      OutboxMutationsCompanion.insert(
        mutationId: mutationId,
        mutationType: 'SET_RATING',
        clientTimestamp: nowIso,
        payloadJson: jsonEncode(payload),
        status: const Value('PENDING'),
      ),
    );

    return UserRatingEntity(
      ratingId: ratingId,
      titleId: titleId,
      ratingValue: ratingValue,
      updatedAt: nowIso,
    );
  }

  Future<List<UserRatingEntity>> getOfflineRatings() async {
    final rows = await _db.getOfflineRatings();
    return rows.map((row) {
      return UserRatingEntity(
        ratingId: row.ratingId,
        titleId: row.titleId,
        ratingValue: row.ratingValue,
        updatedAt: row.ratedAt,
      );
    }).toList();
  }

  Future<UserRatingEntity?> getOfflineRatingForTitle(String titleId) async {
    final row = await _db.getOfflineRatingForTitle(titleId);
    if (row == null) return null;
    return UserRatingEntity(
      ratingId: row.ratingId,
      titleId: row.titleId,
      ratingValue: row.ratingValue,
      updatedAt: row.ratedAt,
    );
  }

  // --------------------------------------------------------------------------
  // Title States & Favorites (Offline-First)
  // --------------------------------------------------------------------------

  Future<UserTitleStateEntity> updateOfflineTitleState({
    required String titleId,
    String? manualStatusOverride,
    bool? isFavorite,
  }) async {
    final existing = await _db.getOfflineTitleState(titleId);
    final nowIso = DateTime.now().toUtc().toIso8601String();

    final finalFav = isFavorite ?? (existing?.isFavorite ?? false);
    final finalStatus = manualStatusOverride ?? existing?.manualStatusOverride;

    await _db.upsertOfflineTitleState(
      OfflineUserTitleStatesCompanion.insert(
        titleId: titleId,
        manualStatusOverride: Value(finalStatus),
        isFavorite: Value(finalFav),
        updatedAt: nowIso,
      ),
    );

    final mutationId = UuidUtil.generateMutationId();
    final payload = {
      'title_id': titleId,
      if (finalStatus != null) 'manual_status_override': finalStatus,
      'is_favorite': finalFav,
      'updated_at': nowIso,
    };

    await _db.insertMutation(
      OutboxMutationsCompanion.insert(
        mutationId: mutationId,
        mutationType: 'UPDATE_TITLE_STATE',
        clientTimestamp: nowIso,
        payloadJson: jsonEncode(payload),
        status: const Value('PENDING'),
      ),
    );

    return UserTitleStateEntity(
      titleId: titleId,
      derivedStatus: finalStatus ?? 'UNWATCHED',
      manualStatusOverride: finalStatus,
      isFavorite: finalFav,
      updatedAt: nowIso,
    );
  }

  Future<List<UserTitleStateEntity>> getOfflineFavorites() async {
    final rows = await _db.getOfflineFavorites();
    return rows.map((row) {
      return UserTitleStateEntity(
        titleId: row.titleId,
        derivedStatus: row.manualStatusOverride ?? 'UNWATCHED',
        manualStatusOverride: row.manualStatusOverride,
        isFavorite: row.isFavorite,
        updatedAt: row.updatedAt,
      );
    }).toList();
  }

  // --------------------------------------------------------------------------
  // Private Personal Notes (Offline-First)
  // --------------------------------------------------------------------------

  Future<UserNoteEntity> addOfflineNote({
    required String titleId,
    required String noteText,
    String? customNoteId,
  }) async {
    final noteId = customNoteId ?? UuidUtil.generateMutationId();
    final nowIso = DateTime.now().toUtc().toIso8601String();

    await _db.upsertOfflineNote(
      OfflineNotesCompanion.insert(
        noteId: noteId,
        titleId: titleId,
        noteText: noteText,
        updatedAt: nowIso,
      ),
    );

    final mutationId = UuidUtil.generateMutationId();
    final payload = {
      'note_id': noteId,
      'title_id': titleId,
      'note_text': noteText,
      'updated_at': nowIso,
    };

    await _db.insertMutation(
      OutboxMutationsCompanion.insert(
        mutationId: mutationId,
        mutationType: 'CREATE_NOTE',
        clientTimestamp: nowIso,
        payloadJson: jsonEncode(payload),
        status: const Value('PENDING'),
      ),
    );

    return UserNoteEntity(
      noteId: noteId,
      titleId: titleId,
      noteText: noteText,
      updatedAt: nowIso,
    );
  }

  Future<List<UserNoteEntity>> getOfflineNotes() async {
    final rows = await _db.getOfflineNotes();
    return rows.map((row) {
      return UserNoteEntity(
        noteId: row.noteId,
        titleId: row.titleId,
        noteText: row.noteText,
        updatedAt: row.updatedAt,
      );
    }).toList();
  }

  // --------------------------------------------------------------------------
  // Non-Authoritative Canonical Title Metadata Cache
  // --------------------------------------------------------------------------

  Future<void> cacheCanonicalTitle({
    required String titleId,
    required String displayId,
    required String primaryTitle,
    required String contentType,
    int? releaseYear,
    String? posterUrl,
    List<String> genres = const [],
  }) async {
    await _db.cacheTitle(
      CachedTitlesCompanion.insert(
        titleId: titleId,
        displayId: displayId,
        primaryTitle: primaryTitle,
        contentType: contentType,
        releaseYear: Value(releaseYear),
        posterUrl: Value(posterUrl),
        genresJson: jsonEncode(genres),
        cachedAt: DateTime.now().toUtc().toIso8601String(),
        isAuthoritative: const Value(false), // Explicitly non-authoritative snapshot
      ),
    );
  }

  Future<CachedTitleRow?> getCachedTitle(String titleId) async {
    return await _db.getCachedTitleById(titleId);
  }
}
