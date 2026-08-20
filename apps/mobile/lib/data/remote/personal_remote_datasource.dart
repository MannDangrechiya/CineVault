// CineVault OS — Personal Library Remote Datasource (8.2)

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
}
