// CineVault OS — Offline Sync Remote Datasource (8.9 / ADR-004)

import '../../core/config/api_config.dart';
import '../../core/network/api_client.dart';
import '../../domain/entities/sync_mutation.dart';

class SyncRemoteDatasource {
  final ApiClient _apiClient;

  SyncRemoteDatasource(this._apiClient);

  Future<SyncPushResultEntity> pushMutations(List<SyncMutationEntity> mutations) async {
    final payload = {
      'mutations': mutations.map((m) => m.toJson()).toList(),
    };

    final response = await _apiClient.dio.post(
      ApiConfig.syncPushEndpoint,
      data: payload,
    );

    return SyncPushResultEntity.fromJson(response.data);
  }

  Future<Map<String, dynamic>> pullDeltas({String? syncCursor, int limit = 50}) async {
    final queryParams = <String, dynamic>{
      'limit': limit,
      if (syncCursor != null) 'sync_cursor': syncCursor,
    };

    final response = await _apiClient.dio.get(
      ApiConfig.syncPullEndpoint,
      queryParameters: queryParams,
    );

    return response.data;
  }
}
