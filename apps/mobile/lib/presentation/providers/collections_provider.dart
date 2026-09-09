// CineVault OS — Collections Riverpod Providers (Part 3.5)

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/remote/collections_remote_datasource.dart';
import '../../data/repositories/collections_repository_impl.dart';
import '../../domain/entities/collections.dart';
import '../../domain/repositories/collections_repository.dart';
import 'catalog_provider.dart' show apiClientProvider;

final collectionsRemoteDatasourceProvider = Provider<CollectionsRemoteDatasource>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return CollectionsRemoteDatasource(apiClient: apiClient);
});

final collectionsRepositoryProvider = Provider<CollectionsRepository>((ref) {
  final remoteDatasource = ref.watch(collectionsRemoteDatasourceProvider);
  return CollectionsRepositoryImpl(remoteDatasource: remoteDatasource);
});

final collectionsListProvider = FutureProvider.autoDispose<List<CollectionEntity>>((ref) {
  return ref.watch(collectionsRepositoryProvider).getCollections();
});

final collectionDetailProvider =
    FutureProvider.autoDispose.family<CollectionDetailEntity, String>((ref, collectionId) {
  return ref.watch(collectionsRepositoryProvider).getCollectionDetail(collectionId);
});
