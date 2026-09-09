// CineVault OS — Collections Remote Datasource (Part 3.5)
// Ports apps/web/src/lib/api/collections.ts 1:1.

import '../../core/config/api_config.dart';
import '../../core/network/api_client.dart';
import '../../domain/entities/collections.dart';

class CollectionsRemoteDatasource {
  final ApiClient _apiClient;

  CollectionsRemoteDatasource({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  Future<List<CollectionEntity>> getCollections() async {
    final response = await _apiClient.dio.get(ApiConfig.personalCollectionsEndpoint);
    final List data = response.data ?? [];
    return data.map((json) => CollectionEntity.fromJson(json)).toList();
  }

  Future<CollectionEntity> createCollection({
    required String name,
    String? description,
    List<String>? tags,
    String? bannerUrl,
    bool isPrivate = false,
  }) async {
    final response = await _apiClient.dio.post(
      ApiConfig.personalCollectionsEndpoint,
      data: {
        'name': name,
        if (description != null) 'description': description,
        if (tags != null) 'tags': tags,
        if (bannerUrl != null) 'banner_url': bannerUrl,
        'is_private': isPrivate,
      },
    );
    return CollectionEntity.fromJson(response.data);
  }

  Future<void> deleteCollection(String id) async {
    await _apiClient.dio.delete('${ApiConfig.personalCollectionsEndpoint}/$id');
  }

  Future<CollectionDetailEntity> getCollectionDetail(String id) async {
    final response = await _apiClient.dio.get('${ApiConfig.personalCollectionsEndpoint}/$id');
    return CollectionDetailEntity.fromJson(response.data);
  }

  Future<CollectionDetailEntity> addCollectionItem({
    required String collectionId,
    required String titleId,
    String? notes,
  }) async {
    final response = await _apiClient.dio.post(
      '${ApiConfig.personalCollectionsEndpoint}/$collectionId/items',
      data: {'title_id': titleId, if (notes != null) 'notes': notes},
    );
    return CollectionDetailEntity.fromJson(response.data);
  }

  Future<void> removeCollectionItem({required String collectionId, required String titleId}) async {
    await _apiClient.dio.delete('${ApiConfig.personalCollectionsEndpoint}/$collectionId/items/$titleId');
  }
}
