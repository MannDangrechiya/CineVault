// CineVault OS — Recommendation Riverpod Provider (8.7)

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/remote/recommendations_remote_datasource.dart';
import '../../domain/entities/recommendation.dart';
import 'catalog_provider.dart';

final recommendationsRemoteDatasourceProvider = Provider<RecommendationsRemoteDatasource>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return RecommendationsRemoteDatasource(apiClient);
});

class RecommendationState {
  final bool isLoading;
  final String activeMode; // tonight, weekend, deep_dive, cold_start
  final List<RecommendationItemEntity> items;
  final String? errorMessage;

  const RecommendationState({
    this.isLoading = false,
    this.activeMode = 'tonight',
    this.items = const [],
    this.errorMessage,
  });

  RecommendationState copyWith({
    bool? isLoading,
    String? activeMode,
    List<RecommendationItemEntity>? items,
    String? errorMessage,
  }) {
    return RecommendationState(
      isLoading: isLoading ?? this.isLoading,
      activeMode: activeMode ?? this.activeMode,
      items: items ?? this.items,
      errorMessage: errorMessage,
    );
  }
}

class RecommendationNotifier extends StateNotifier<RecommendationState> {
  final RecommendationsRemoteDatasource _datasource;

  RecommendationNotifier(this._datasource) : super(const RecommendationState()) {
    fetchRecommendations('tonight');
  }

  Future<void> fetchRecommendations(String mode) async {
    state = state.copyWith(isLoading: true, activeMode: mode, errorMessage: null);
    try {
      final results = await _datasource.getPersonalizedRecommendations(mode: mode);
      state = state.copyWith(isLoading: false, items: results);
    } catch (e) {
      state = state.copyWith(isLoading: false, errorMessage: e.toString());
    }
  }
}

final recommendationProvider = StateNotifierProvider<RecommendationNotifier, RecommendationState>((ref) {
  final datasource = ref.watch(recommendationsRemoteDatasourceProvider);
  return RecommendationNotifier(datasource);
});

final similarTitlesProvider = FutureProvider.family<List<RecommendationItemEntity>, String>((ref, titleId) async {
  final datasource = ref.watch(recommendationsRemoteDatasourceProvider);
  return await datasource.getSimilarTitles(titleId);
});
