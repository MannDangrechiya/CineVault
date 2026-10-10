// CineVault OS — Import Riverpod Provider (Part 3.9)

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/remote/import_remote_datasource.dart';
import 'catalog_provider.dart' show apiClientProvider;

final importRemoteDatasourceProvider = Provider<ImportRemoteDatasource>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return ImportRemoteDatasource(apiClient: apiClient);
});
