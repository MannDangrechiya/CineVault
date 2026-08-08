// CineVault OS — Sync Outbox Riverpod Provider (8.9 / ADR-004)

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/local/app_database.dart';
import '../../data/remote/sync_remote_datasource.dart';
import '../../data/repositories/sync_repository_impl.dart';
import '../../domain/entities/sync_mutation.dart';
import 'catalog_provider.dart';

final appDatabaseProvider = Provider<AppDatabase>((ref) => AppDatabase());

final syncRemoteDatasourceProvider = Provider<SyncRemoteDatasource>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return SyncRemoteDatasource(apiClient);
});

final syncRepositoryProvider = Provider<SyncRepositoryImpl>((ref) {
  final db = ref.watch(appDatabaseProvider);
  final remote = ref.watch(syncRemoteDatasourceProvider);
  return SyncRepositoryImpl(db, remote);
});

class SyncState {
  final bool isSyncing;
  final List<SyncMutationEntity> pendingMutations;
  final String? lastSyncTimestamp;
  final String? errorMessage;

  const SyncState({
    this.isSyncing = false,
    this.pendingMutations = const [],
    this.lastSyncTimestamp,
    this.errorMessage,
  });

  SyncState copyWith({
    bool? isSyncing,
    List<SyncMutationEntity>? pendingMutations,
    String? lastSyncTimestamp,
    String? errorMessage,
  }) {
    return SyncState(
      isSyncing: isSyncing ?? this.isSyncing,
      pendingMutations: pendingMutations ?? this.pendingMutations,
      lastSyncTimestamp: lastSyncTimestamp ?? this.lastSyncTimestamp,
      errorMessage: errorMessage,
    );
  }
}

class SyncNotifier extends StateNotifier<SyncState> {
  final SyncRepositoryImpl _repository;

  SyncNotifier(this._repository) : super(const SyncState()) {
    loadPendingMutations();
  }

  Future<void> loadPendingMutations() async {
    try {
      final pending = await _repository.getPendingMutations();
      state = state.copyWith(pendingMutations: pending);
    } catch (_) {}
  }

  Future<void> queueAndSync({
    required String mutationType,
    required Map<String, dynamic> payload,
  }) async {
    await _repository.queueMutation(mutationType: mutationType, payload: payload);
    await loadPendingMutations();
    await triggerSyncPush();
  }

  Future<void> triggerSyncPush() async {
    state = state.copyWith(isSyncing: true, errorMessage: null);
    try {
      await _repository.processOutboxSync();
      final remaining = await _repository.getPendingMutations();
      state = state.copyWith(
        isSyncing: false,
        pendingMutations: remaining,
        lastSyncTimestamp: DateTime.now().toIso8601String(),
      );
    } catch (e) {
      state = state.copyWith(
        isSyncing: false,
        errorMessage: e.toString(),
      );
    }
  }
}

final syncProvider = StateNotifierProvider<SyncNotifier, SyncState>((ref) {
  final repository = ref.watch(syncRepositoryProvider);
  return SyncNotifier(repository);
});
