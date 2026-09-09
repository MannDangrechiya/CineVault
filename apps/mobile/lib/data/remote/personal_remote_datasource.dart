// CineVault OS — Personal Library Remote Datasource (8.2)

import 'package:dio/dio.dart';
import '../../core/config/api_config.dart';
import '../../core/network/api_client.dart';
import '../../domain/entities/personal.dart';

class PersonalRemoteDatasource {
  final ApiClient _apiClient;

  PersonalRemoteDatasource(this._apiClient);

  Future<List<WatchEventEntity>> getWatchHistory() async {
    final response = await _apiClient.dio.get(ApiConfig.watchEventsEndpoint);
    // Backend returns PaginatedResponse[WatchEventResponse] with 'data' field
    final List data = response.data['data'] ?? response.data['watch_events'] ?? [];
    return data.map((json) => WatchEventEntity.fromJson(json)).toList();
  }

  Future<WatchEventEntity> createWatchEvent({
    required String titleId,
    required String watchedAt,
    double progressPercentage = 100.0,
    String? editionId,
  }) async {
    // Match backend WatchEventCreate schema
    final payload = {
      'title_id': titleId,
      'watched_at': watchedAt,
      'progress_percentage': progressPercentage,
      if (editionId != null) 'edition_id': editionId,
    };

    final response = await _apiClient.dio.post(
      ApiConfig.watchEventsEndpoint,
      data: payload,
    );

    return WatchEventEntity.fromJson(response.data);
  }

  Future<UserRatingEntity> setRating({
    required String titleId,
    required int ratingValue,
  }) async {
    // Match backend RatingCreate schema (title_id + rating_value only)
    final payload = {
      'title_id': titleId,
      'rating_value': ratingValue,
    };

    final response = await _apiClient.dio.post(
      ApiConfig.ratingsEndpoint,
      data: payload,
    );

    return UserRatingEntity.fromJson(response.data);
  }

  Future<UserNoteEntity> upsertNote({
    required String titleId,
    required String noteText,
  }) async {
    // Match backend NoteCreate schema (title_id + note_text only)
    final payload = {
      'title_id': titleId,
      'note_text': noteText,
    };

    final response = await _apiClient.dio.post(
      ApiConfig.notesEndpoint,
      data: payload,
    );

    return UserNoteEntity.fromJson(response.data);
  }

  // ── Reviews (Part 3, closes a gap left by the original 8.2 datasource) ──

  Future<List<ReviewEntity>> getUserReviews({String? titleId}) async {
    final response = await _apiClient.dio.get(
      ApiConfig.reviewsEndpoint,
      queryParameters: titleId != null ? {'title_id': titleId} : null,
    );
    final List data = response.data ?? [];
    return data.map((json) => ReviewEntity.fromJson(json)).toList();
  }

  Future<ReviewEntity> createUserReview({
    required String titleId,
    required String reviewTitle,
    required String reviewText,
    bool isPublic = true,
  }) async {
    final response = await _apiClient.dio.post(
      ApiConfig.reviewsEndpoint,
      data: {
        'title_id': titleId,
        'review_title': reviewTitle,
        'review_text': reviewText,
        'is_public': isPublic,
      },
    );
    return ReviewEntity.fromJson(response.data);
  }

  Future<void> deleteUserReview(String reviewId) async {
    await _apiClient.dio.delete('${ApiConfig.reviewsEndpoint}/$reviewId');
  }

  // ── Watchlist (Part 3.4) ──────────────────────────────────────────────
  // Maps onto the title-state system: PATCH manual_status_override to
  // PLAN_TO_WATCH to add, explicit null to remove (backend treats an
  // explicit null as "clear", distinct from an omitted field).

  Future<List<WatchlistItemEntity>> getWatchlist() async {
    final response = await _apiClient.dio.get(
      ApiConfig.personalWatchlistEndpoint,
      queryParameters: {'limit': 100},
    );
    final List data = response.data['items'] ?? [];
    return data.map((json) => WatchlistItemEntity.fromJson(json)).toList();
  }

  Future<bool> toggleWatchlistState({required String titleId, required bool inWatchlist}) async {
    final response = await _apiClient.dio.patch(
      '${ApiConfig.titleStatesEndpoint}/$titleId',
      data: {'manual_status_override': inWatchlist ? 'PLAN_TO_WATCH' : null},
    );
    return response.data['manual_status_override'] == 'PLAN_TO_WATCH';
  }

  // ── Watch History (Part 3.4) ──────────────────────────────────────────

  Future<List<HistoryItemEntity>> getHistory({int limit = 50, int offset = 0, String? type}) async {
    final response = await _apiClient.dio.get(
      ApiConfig.personalHistoryEndpoint,
      queryParameters: {
        'limit': limit,
        'offset': offset,
        if (type != null && type != 'ALL') 'type': type,
      },
    );
    final List data = response.data['items'] ?? [];
    return data.map((json) => HistoryItemEntity.fromJson(json)).toList();
  }

  Future<void> deleteHistoryItem(String id) async {
    await _apiClient.dio.delete('${ApiConfig.personalHistoryEndpoint}/$id');
  }

  // ── Dashboard: streak & analytics (Part 3.3) ──────────────────────────

  Future<UserStreakEntity> getUserStreak() async {
    final response = await _apiClient.dio.get(ApiConfig.personalStreakEndpoint);
    return UserStreakEntity.fromJson(response.data);
  }

  Future<PersonalAnalyticsEntity> getPersonalAnalytics() async {
    final response = await _apiClient.dio.get(ApiConfig.personalAnalyticsEndpoint);
    return PersonalAnalyticsEntity.fromJson(response.data);
  }

  // ── Data Export (Settings screen) ─────────────────────────────────────
  // Matches web's downloadExport() — GET /v1/personal/export?format=X
  // returns the raw file bytes for the requested format directly (no JSON
  // envelope), so this uses responseType: bytes rather than the default
  // json-decoding path every other method here relies on.

  Future<List<int>> exportPersonalData({required String format}) async {
    final response = await _apiClient.dio.get<List<int>>(
      ApiConfig.personalExportEndpoint,
      queryParameters: {'format': format, 'download': true},
      options: Options(responseType: ResponseType.bytes),
    );
    return response.data ?? const [];
  }
}
