// CineVault OS — Auto-Sync Reconnect Unit & Widget Tests (Phase 9.9)

import 'package:flutter_test/flutter_test.dart';
import 'package:cinevault_client/core/network/connectivity_service.dart';
import 'package:cinevault_client/presentation/providers/sync_provider.dart';
import 'package:cinevault_client/data/repositories/sync_repository_impl.dart';
import 'package:cinevault_client/domain/entities/sync_mutation.dart';

class FakeSyncRepository implements SyncRepositoryImpl {
  int syncPushCallCount = 0;
  List<SyncMutationEntity> mutations = [];

  @override
  Future<List<SyncMutationEntity>> getPendingMutations() async => mutations;

  @override
  Future<SyncMutationEntity> queueMutation({required String mutationType, required Map<String, dynamic> payload}) async {
    final entity = SyncMutationEntity(
      mutationId: 'mut_001',
      mutationType: mutationType,
      payload: payload,
      clientTimestamp: '2026-08-09T00:00:00Z',
      status: 'PENDING',
    );
    mutations.add(entity);
    return entity;
  }

  @override
  Future<SyncPushResultEntity> processOutboxSync() async {
    syncPushCallCount++;
    mutations.clear();
    return const SyncPushResultEntity(
      processedCount: 1,
      acknowledgedMutationIds: ['mut_001'],
      failedMutations: [],
    );
  }
}

void main() {
  test('ConnectivityService fires reconnect event on offline to online transition', () async {
    final service = ConnectivityService(initialOnline: false);
    int reconnectEventCount = 0;

    service.reconnectStream.listen((_) {
      reconnectEventCount++;
    });

    service.updateConnectivity(true);
    await Future.delayed(const Duration(milliseconds: 1100));

    expect(reconnectEventCount, equals(1));
    service.dispose();
  });

  test('ConnectivityService debounces flapping connection state changes', () async {
    final service = ConnectivityService(initialOnline: false);
    int reconnectEventCount = 0;

    service.reconnectStream.listen((_) {
      reconnectEventCount++;
    });

    // Flapping status updates rapidly
    service.updateConnectivity(true);
    service.updateConnectivity(false);
    service.updateConnectivity(true);
    service.updateConnectivity(false);
    service.updateConnectivity(true);

    await Future.delayed(const Duration(milliseconds: 1100));

    // Must fire debounced reconnect call exactly once
    expect(reconnectEventCount, equals(1));
    service.dispose();
  });

  test('SyncNotifier automatically triggers sync push on debounced reconnect', () async {
    final fakeRepo = FakeSyncRepository();
    final connectivity = ConnectivityService(initialOnline: false);
    final notifier = SyncNotifier(fakeRepo, connectivity);

    expect(fakeRepo.syncPushCallCount, equals(0));

    // Transition offline -> online
    connectivity.updateConnectivity(true);
    await Future.delayed(const Duration(milliseconds: 1200));

    expect(fakeRepo.syncPushCallCount, equals(1));

    notifier.dispose();
    connectivity.dispose();
  });
}
