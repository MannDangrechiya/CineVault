// CineVault OS — Personal Domain Riverpod Providers (Part 3.3/3.4)
// Streak, analytics, watchlist & history reads backed by the remote API —
// distinct from personal_offline_repository.dart's local Drift-backed
// providers (defined per-screen), which serve the device's offline cache.

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/remote/personal_remote_datasource.dart';
import '../../domain/entities/personal.dart';
import 'catalog_provider.dart' show apiClientProvider;

final personalRemoteDatasourceProvider = Provider<PersonalRemoteDatasource>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return PersonalRemoteDatasource(apiClient);
});

final userStreakProvider = FutureProvider.autoDispose<UserStreakEntity>((ref) {
  return ref.watch(personalRemoteDatasourceProvider).getUserStreak();
});

final personalAnalyticsProvider = FutureProvider.autoDispose<PersonalAnalyticsEntity>((ref) {
  return ref.watch(personalRemoteDatasourceProvider).getPersonalAnalytics();
});

final remoteWatchlistProvider = FutureProvider.autoDispose<List<WatchlistItemEntity>>((ref) {
  return ref.watch(personalRemoteDatasourceProvider).getWatchlist();
});

final remoteHistoryProvider = FutureProvider.autoDispose<List<HistoryItemEntity>>((ref) {
  return ref.watch(personalRemoteDatasourceProvider).getHistory();
});
