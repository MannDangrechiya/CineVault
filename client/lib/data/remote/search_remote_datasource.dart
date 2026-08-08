// CineVault OS — Search Remote Datasource (8.3)

import 'package:dio/dio.dart';
import '../../core/config/api_config.dart';
import '../../core/network/api_client.dart';
import '../../domain/entities/title.dart';

class SearchRemoteDatasource {
  final ApiClient _apiClient;

  SearchRemoteDatasource(this._apiClient);

  Future<List<CanonicalTitleEntity>> searchCatalog({
    required String query,
    String? type,
    int? year,
    int limit = 20,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'q': query,
        'limit': limit,
        if (type != null) 'type': type,
        if (year != null) 'year': year,
      };

      final response = await _apiClient.dio.get(
        ApiConfig.searchEndpoint,
        queryParameters: queryParams,
      );

      final List data = response.data['results'] ?? response.data['items'] ?? response.data ?? [];
      return data.map((json) => CanonicalTitleEntity.fromJson(json)).toList();
    } on DioException catch (e) {
      throw _apiClient.mapDioErrorToFailure(e);
    }
  }
}
