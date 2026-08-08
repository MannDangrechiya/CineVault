// CineVault OS — Personal Library Remote Datasource (8.2)

import 'package:dio/dio.dart';
import '../../core/config/api_config.dart';
import '../../core/network/api_client.dart';
import '../../domain/entities/personal.dart';

class PersonalRemoteDatasource {
  final ApiClient _apiClient;

  PersonalRemoteDatasource(this._apiClient);

  Future<List<WatchEventEntity>> getWatchHistory() async {
    try {
      final response = await _apiClient.dio.get('${ApiConfig.meLibraryEndpoint}/watch-events');
      final List data = response.data['watch_events'] ?? response.data ?? [];
      return data.map((json) => WatchEventEntity.fromJson(json)).toList();
    } on DioException catch (e) {
      throw _apiClient.mapDioErrorToFailure(e);
    }
  }

  Future<WatchEventEntity> createWatchEvent({
    required String titleId,
    required String watchMode,
    double? ratingValue,
    String? notes,
  }) async {
    try {
      final payload = {
        'title_id': titleId,
        'watch_mode': watchMode,
        if (ratingValue != null) 'rating_value': ratingValue,
        if (notes != null) 'notes': notes,
      };

      final response = await _apiClient.dio.post(
        ApiConfig.watchEventsEndpoint,
        data: payload,
      );

      return WatchEventEntity.fromJson(response.data);
    } on DioException catch (e) {
      throw _apiClient.mapDioErrorToFailure(e);
    }
  }

  Future<UserRatingEntity> setRating({
    required String titleId,
    required double ratingValue,
    String? reviewText,
  }) async {
    try {
      final payload = {
        'title_id': titleId,
        'rating_value': ratingValue,
        if (reviewText != null) 'review_text': reviewText,
      };

      final response = await _apiClient.dio.post(
        ApiConfig.ratingsEndpoint,
        data: payload,
      );

      return UserRatingEntity.fromJson(response.data);
    } on DioException catch (e) {
      throw _apiClient.mapDioErrorToFailure(e);
    }
  }

  Future<UserNoteEntity> upsertNote({
    required String titleId,
    required String noteContent,
    bool isPrivate = true,
  }) async {
    try {
      final payload = {
        'title_id': titleId,
        'note_content': noteContent,
        'is_private': isPrivate,
      };

      final response = await _apiClient.dio.post(
        ApiConfig.notesEndpoint,
        data: payload,
      );

      return UserNoteEntity.fromJson(response.data);
    } on DioException catch (e) {
      throw _apiClient.mapDioErrorToFailure(e);
    }
  }
}
