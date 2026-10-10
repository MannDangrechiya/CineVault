// CineVault OS — Collections Repository Implementation (Part 3.5)

import '../../domain/entities/collections.dart';
import '../../domain/repositories/collections_repository.dart';
import '../remote/collections_remote_datasource.dart';

class CollectionsRepositoryImpl implements CollectionsRepository {
  final CollectionsRemoteDatasource _remoteDatasource;

  CollectionsRepositoryImpl({CollectionsRemoteDatasource? remoteDatasource})
      : _remoteDatasource = remoteDatasource ?? CollectionsRemoteDatasource();

  @override
  Future<List<CollectionEntity>> getCollections() => _remoteDatasource.getCollections();

  @override
  Future<CollectionEntity> createCollection({
    required String name,
    String? description,
    List<String>? tags,
    String? bannerUrl,
    bool isPrivate = false,
  }) =>
      _remoteDatasource.createCollection(
        name: name,
        description: description,
        tags: tags,
        bannerUrl: bannerUrl,
        isPrivate: isPrivate,
      );

  @override
  Future<void> deleteCollection(String id) => _remoteDatasource.deleteCollection(id);

  @override
  Future<CollectionDetailEntity> getCollectionDetail(String id) =>
      _remoteDatasource.getCollectionDetail(id);

  @override
  Future<CollectionDetailEntity> addCollectionItem({
    required String collectionId,
    required String titleId,
    String? notes,
  }) =>
      _remoteDatasource.addCollectionItem(collectionId: collectionId, titleId: titleId, notes: notes);

  @override
  Future<void> removeCollectionItem({required String collectionId, required String titleId}) =>
      _remoteDatasource.removeCollectionItem(collectionId: collectionId, titleId: titleId);
}
