// CineVault OS — Catalog Riverpod Provider (8.1)

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/api_client.dart';
import '../../data/remote/titles_remote_datasource.dart';
import '../../domain/entities/title.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

final titlesRemoteDatasourceProvider = Provider<TitlesRemoteDatasource>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return TitlesRemoteDatasource(apiClient);
});

class CatalogState {
  final bool isLoading;
  final List<CanonicalTitleEntity> titles;
  final String? errorMessage;
  final String? selectedContentType;
  final int? selectedProductionYear;
  final String? selectedOriginCountry;

  const CatalogState({
    this.isLoading = false,
    this.titles = const [],
    this.errorMessage,
    this.selectedContentType,
    this.selectedProductionYear,
    this.selectedOriginCountry,
  });

  CatalogState copyWith({
    bool? isLoading,
    List<CanonicalTitleEntity>? titles,
    String? errorMessage,
    String? selectedContentType,
    int? selectedProductionYear,
    String? selectedOriginCountry,
  }) {
    return CatalogState(
      isLoading: isLoading ?? this.isLoading,
      titles: titles ?? this.titles,
      errorMessage: errorMessage,
      selectedContentType: selectedContentType ?? this.selectedContentType,
      selectedProductionYear: selectedProductionYear ?? this.selectedProductionYear,
      selectedOriginCountry: selectedOriginCountry ?? this.selectedOriginCountry,
    );
  }
}

class CatalogNotifier extends StateNotifier<CatalogState> {
  final TitlesRemoteDatasource _datasource;

  CatalogNotifier(this._datasource) : super(const CatalogState()) {
    fetchTitles();
  }

  Future<void> fetchTitles({
    String? contentType,
    int? productionYear,
    String? originCountry,
  }) async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final items = await _datasource.listTitles(
        contentType: contentType ?? state.selectedContentType,
        productionYear: productionYear ?? state.selectedProductionYear,
        originCountry: originCountry ?? state.selectedOriginCountry,
      );
      state = state.copyWith(
        isLoading: false,
        titles: items,
        selectedContentType: contentType ?? state.selectedContentType,
        selectedProductionYear: productionYear ?? state.selectedProductionYear,
        selectedOriginCountry: originCountry ?? state.selectedOriginCountry,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: e.toString(),
      );
    }
  }
}

final catalogProvider = StateNotifierProvider<CatalogNotifier, CatalogState>((ref) {
  final datasource = ref.watch(titlesRemoteDatasourceProvider);
  return CatalogNotifier(datasource);
});

final titleDetailProvider = FutureProvider.family<CanonicalTitleEntity, String>((ref, titleId) async {
  final datasource = ref.watch(titlesRemoteDatasourceProvider);
  return await datasource.getTitleDetail(titleId);
});

final titleAvailabilityProvider = FutureProvider.family<List<AvailabilityEntity>, String>((ref, titleId) async {
  final datasource = ref.watch(titlesRemoteDatasourceProvider);
  return await datasource.getTitleAvailability(titleId);
});
