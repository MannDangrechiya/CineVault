// CineVault OS — Offline Sync Status Screen (Phase 9.9 / ADR-004)
// Outbox queue inspector, connection state monitoring, and auto-sync / manual push triggers

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../providers/sync_provider.dart';
import '../widgets/glass/glass.dart';

class SyncStatusScreen extends ConsumerWidget {
  const SyncStatusScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final syncState = ref.watch(syncProvider);
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: GlassAppBar(
        title: const Text('Offline Sync Status (ADR-004)'),
        actions: [
          IconButton(
            icon: const Icon(Icons.sync),
            tooltip: 'Trigger sync push',
            onPressed: () => ref.read(syncProvider.notifier).triggerSyncPush(),
          ),
        ],
      ),
      body: Column(
        children: [
          GlassAppBar.contentSpacer(context),
          // Connection Status Banner
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Align(
              alignment: Alignment.centerLeft,
              child: GlassBadge(
                label: syncState.isOnline
                    ? 'Online Mode — Auto-sync on reconnect active'
                    : 'Offline Mode — Outbox changes queued locally',
                tint: syncState.isOnline
                    ? AppTheme.stateSuccess
                    : AppTheme.stateWarning,
                icon: syncState.isOnline ? Icons.wifi : Icons.wifi_off,
              ),
            ),
          ),

          // Header Card
          SizedBox(
            width: double.infinity,
            child: GlassContainer(
              blurTier: GlassBlurTier.sm,
              borderRadius: BorderRadius.zero,
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        syncState.pendingMutations.isEmpty
                            ? Icons.check_circle
                            : Icons.cloud_upload_outlined,
                        color: syncState.pendingMutations.isEmpty
                            ? AppTheme.stateSuccess
                            : AppTheme.stateWarning,
                        size: 28,
                      ),
                      const SizedBox(width: 10),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            syncState.pendingMutations.isEmpty
                                ? 'Outbox Queue Clean'
                                : '${syncState.pendingMutations.length} Outbox Mutations Pending',
                            style: textTheme.titleMedium,
                          ),
                          Text(
                            syncState.lastSyncTimestamp != null
                                ? 'Last Synced: ${syncState.lastSyncTimestamp}'
                                : 'No sync performed yet this session.',
                            style: textTheme.bodySmall,
                          ),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      icon: syncState.isSyncing
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : const Icon(Icons.sync),
                      label: Text(
                        syncState.isSyncing
                            ? 'Syncing Outbox...'
                            : 'Push Pending Outbox Mutations',
                      ),
                      onPressed: syncState.isSyncing
                          ? null
                          : () => ref
                                .read(syncProvider.notifier)
                                .triggerSyncPush(),
                    ),
                  ),
                ],
              ),
            ),
          ),

          if (syncState.errorMessage != null)
            GlassCard(
              margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              tintColor: AppTheme.stateError,
              child: Row(
                children: [
                  const Icon(Icons.error_outline, color: AppTheme.stateError),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      syncState.errorMessage!,
                      style: const TextStyle(color: AppTheme.stateError),
                    ),
                  ),
                ],
              ),
            ),

          // Pending Items List
          Expanded(
            child: syncState.pendingMutations.isEmpty
                ? Center(
                    child: GlassCard(
                      margin: const EdgeInsets.all(24.0),
                      padding: const EdgeInsets.all(24.0),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(
                            Icons.cloud_done_outlined,
                            size: 64,
                            color: AppTheme.stateSuccess,
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'All offline actions acknowledged by server.',
                            style: textTheme.titleMedium,
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            'Mutations queued while offline will appear here in the durable outbox before server sync.',
                            style: TextStyle(color: AppTheme.textMuted),
                            textAlign: TextAlign.center,
                          ),
                        ],
                      ),
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: syncState.pendingMutations.length,
                    itemBuilder: (context, index) {
                      final item = syncState.pendingMutations[index];
                      return GlassCard(
                        margin: const EdgeInsets.only(bottom: 10),
                        padding: EdgeInsets.zero,
                        child: ListTile(
                          leading: const Icon(
                            Icons.pending_actions,
                            color: AppTheme.primaryLightViolet,
                          ),
                          title: Text(
                            'Mutation: ${item.mutationType}',
                            style: textTheme.titleMedium,
                          ),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'ID: ${item.mutationId}',
                                style: const TextStyle(
                                  fontSize: 11,
                                  fontFamily: 'monospace',
                                ),
                              ),
                              Text(
                                'Recorded: ${item.clientTimestamp}',
                                style: textTheme.bodySmall,
                              ),
                            ],
                          ),
                          trailing: GlassBadge(
                            label: item.status,
                            tint: AppTheme.stateWarning,
                          ),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
