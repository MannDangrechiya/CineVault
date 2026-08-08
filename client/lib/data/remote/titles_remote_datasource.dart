// CineVault OS — Canonical Titles Remote Datasource (8.1, 8.6)

import 'package:dio/dio.dart';
import '../../core/config/api_config.dart';
import '../../core/network/api_client.dart';
import '../../domain/entities/title.dart';

class TitlesRemoteDatasource {
  final ApiClient _apiClient;

  TitlesRemoteDatasource(this._apiClient);

  Future<List<CanonicalTitleEntity>> listTitles({
    int limit = 20,
    String? cursor,
    String? contentType,
    int? year,
    String? country,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'limit': limit,
        if (cursor != null) 'cursor': cursor,
        if (contentType != null) 'content_type': contentType,
        if (year != null) 'year': year,
        if (country != null) 'country': country,
      };

      final response = await _apiClient.dio.get(
        ApiConfig.titlesEndpoint,
        queryParameters: queryParams,
      );

      final List data = response.data['items'] ?? response.data ?? [];
      return data.map((json) => CanonicalTitleEntity.fromJson(json)).toList();
    } on DioException catch (e) {
      throw _apiClient.mapDioErrorToFailure(e);
    }
  }

  Future<CanonicalTitleEntity> getTitleDetail(String titleId) async {
    try {
      final response = await _apiClient.dio.get('${ApiConfig.titlesEndpoint}/$titleId');
      return CanonicalTitleEntity.fromJson(response.data);
    } on DioException catch (e) {
      throw _apiClient.mapDioErrorToFailure(e);
    }
  }

  Future<List<AvailabilityEntity>> getTitleAvailability(String titleId) async {
    try {
      final response = await _apiClient.dio.get('${ApiConfig.titlesEndpoint}/$titleId/availability');
      final List data = response.data['availabilities'] ?? response.data ?? [];
      return data.map((json) => AvailabilityEntity.fromJson(json)).toList();
    } on DioException catch (e) {
      throw _apiClient.mapDioErrorToFailure(e);
    }
  }

  Future<List<ReleaseEntity>> getTitleReleases(String titleId) async {
    try {
      final response = await _apiClient.dio.get('${ApiConfig.titlesEndpoint}/$titleId/releases');
      final List data = response.data['releases'] ?? response.data ?? [];
      return data.map((json) => ReleaseEntity.fromJson(json)).toList();
    } on DioException catch (e) {
      throw _apiClient.mapDioErrorToFailure(e);
    }
  }
}
