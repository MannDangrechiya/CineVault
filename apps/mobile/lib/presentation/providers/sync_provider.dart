// CineVault OS — Sync Outbox Riverpod Provider & Auto-Sync Listener (Phase 9.9 / ADR-004)

import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/connectivity_service.dart';
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
  final bool isOnline;
  final List<SyncMutationEntity> pendingMutations;
  final String? lastSyncTimestamp;
  final String? errorMessage;

  const SyncState({
    this.isSyncing = false,
    this.isOnline = true,
    this.pendingMutations = const [],
    this.lastSyncTimestamp,
    this.errorMessage,
  });

  SyncState copyWith({
    bool? isSyncing,
    bool? isOnline,
    List<SyncMutationEntity>? pendingMutations,
    String? lastSyncTimestamp,
    String? errorMessage,
  }) {
    return SyncState(
      isSyncing: isSyncing ?? this.isSyncing,
      isOnline: isOnline ?? this.isOnline,
      pendingMutations: pendingMutations ?? this.pendingMutations,
      lastSyncTimestamp: lastSyncTimestamp ?? this.lastSyncTimestamp,
      errorMessage: errorMessage,
    );
  }
}

class SyncNotifier extends StateNotifier<SyncState> {
  final SyncRepositoryImpl _repository;
  final ConnectivityService? _connectivityService;
  StreamSubscription<void>? _reconnectSub;
  StreamSubscription<bool>? _statusSub;

  SyncNotifier(this._repository, [this._connectivityService]) : super(const SyncState()) {
    loadPendingMutations();
    if (_connectivityService != null) {
      state = state.copyWith(isOnline: _connectivityService.isOnline);
      _statusSub = _connectivityService.statusStream.listen((online) {
        state = state.copyWith(isOnline: online);
      });
      _reconnectSub = _connectivityService.reconnectStream.listen((_) {
        triggerSyncPush();
      });
    }
  }

  @override
  void dispose() {
    _statusSub?.cancel();
    _reconnectSub?.cancel();
    super.dispose();
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
    if (state.isOnline) {
      await triggerSyncPush();
    }
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
  final connectivity = ref.watch(connectivityServiceProvider);
  return SyncNotifier(repository, connectivity);
});
