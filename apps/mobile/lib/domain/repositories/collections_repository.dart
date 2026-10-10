// CineVault OS — Collections Repository Interface (Part 3.5)

import '../entities/collections.dart';

abstract class CollectionsRepository {
  Future<List<CollectionEntity>> getCollections();
  Future<CollectionEntity> createCollection({
    required String name,
    String? description,
    List<String>? tags,
    String? bannerUrl,
    bool isPrivate,
  });
  Future<void> deleteCollection(String id);
  Future<CollectionDetailEntity> getCollectionDetail(String id);
  Future<CollectionDetailEntity> addCollectionItem({
    required String collectionId,
    required String titleId,
    String? notes,
  });
  Future<void> removeCollectionItem({required String collectionId, required String titleId});
}
