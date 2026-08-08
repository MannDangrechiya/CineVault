// CineVault OS — Recommendation Remote Datasource (8.7)

import 'package:dio/dio.dart';
import '../../core/config/api_config.dart';
import '../../core/network/api_client.dart';
import '../../domain/entities/recommendation.dart';

class RecommendationsRemoteDatasource {
  final ApiClient _apiClient;

  RecommendationsRemoteDatasource(this._apiClient);

  Future<List<RecommendationItemEntity>> getPersonalizedRecommendations({
    String mode = 'tonight',
    int? maxRuntime,
    String? genre,
    bool availableOnly = true,
    bool includeWatched = false,
    String? seedTitleId,
    int limit = 10,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'mode': mode,
        'limit': limit,
        'available_only': availableOnly,
        'include_watched': includeWatched,
        if (maxRuntime != null) 'max_runtime': maxRuntime,
        if (genre != null) 'genre': genre,
        if (seedTitleId != null) 'seed_title_id': seedTitleId,
      };

      final response = await _apiClient.dio.get(
        ApiConfig.recommendationsEndpoint,
        queryParameters: queryParams,
      );

      final List data = response.data['items'] ?? response.data['recommendations'] ?? [];
      return data.map((json) => RecommendationItemEntity.fromJson(json)).toList();
    } on DioException catch (e) {
      throw _apiClient.mapDioErrorToFailure(e);
    }
  }

  Future<List<RecommendationItemEntity>> getColdStartRecommendations({
    required List<String> preferredGenres,
    required List<String> seedTitleIds,
    int limit = 10,
  }) async {
    try {
      final payload = {
        'preferred_genres': preferredGenres,
        'seed_title_ids': seedTitleIds,
      };

      final response = await _apiClient.dio.post(
        ApiConfig.coldStartRecommendationsEndpoint,
        data: payload,
        queryParameters: {'limit': limit},
      );

      final List data = response.data['items'] ?? response.data['recommendations'] ?? [];
      return data.map((json) => RecommendationItemEntity.fromJson(json)).toList();
    } on DioException catch (e) {
      throw _apiClient.mapDioErrorToFailure(e);
    }
  }

  Future<List<RecommendationItemEntity>> getSimilarTitles(String titleId, {int limit = 5}) async {
    try {
      final response = await _apiClient.dio.get(
        '${ApiConfig.recommendationsEndpoint}/similar/$titleId',
        queryParameters: {'limit': limit},
      );

      final List data = response.data['items'] ?? response.data['recommendations'] ?? [];
      return data.map((json) => RecommendationItemEntity.fromJson(json)).toList();
    } on DioException catch (e) {
      throw _apiClient.mapDioErrorToFailure(e);
    }
  }

  Future<GroundedExplanationEntity> explainRecommendation({
    required String titleId,
    String? seedTitleId,
  }) async {
    try {
      final payload = {
        'title_id': titleId,
        if (seedTitleId != null) 'seed_title_id': seedTitleId,
      };

      final response = await _apiClient.dio.post(
        ApiConfig.explainRecommendationEndpoint,
        data: payload,
      );

      return GroundedExplanationEntity.fromJson(response.data);
    } on DioException catch (e) {
      throw _apiClient.mapDioErrorToFailure(e);
    }
  }
}
