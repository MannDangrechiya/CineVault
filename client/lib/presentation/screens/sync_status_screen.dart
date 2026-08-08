// CineVault OS — Offline Sync Status Screen (8.9 / ADR-004)
// Outbox queue inspector, mutation state tracking, and manual push sync triggers

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../providers/sync_provider.dart';

class SyncStatusScreen extends ConsumerWidget {
  const SyncStatusScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final syncState = ref.watch(syncProvider);
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(
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
          // Header Card
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            color: AppTheme.cardSurface,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(
                      syncState.pendingMutations.isEmpty ? Icons.check_circle : Icons.cloud_upload_outlined,
                      color: syncState.pendingMutations.isEmpty ? AppTheme.stateSuccess : AppTheme.stateWarning,
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
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : const Icon(Icons.sync),
                    label: Text(syncState.isSyncing ? 'Syncing Outbox...' : 'Push Pending Outbox Mutations'),
                    onPressed: syncState.isSyncing
                        ? null
                        : () => ref.read(syncProvider.notifier).triggerSyncPush(),
                  ),
                ),
              ],
            ),
          ),

          if (syncState.errorMessage != null)
            Container(
              padding: const EdgeInsets.all(12),
              color: AppTheme.stateError.withValues(alpha: 0.15),
              child: Row(
                children: [
                  const Icon(Icons.error_outline, color: AppTheme.stateError),
                  const SizedBox(width: 8),
                  Expanded(child: Text(syncState.errorMessage!, style: const TextStyle(color: AppTheme.stateError))),
                ],
              ),
            ),

          // Pending Items List
          Expanded(
            child: syncState.pendingMutations.isEmpty
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24.0),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.cloud_done_outlined, size: 64, color: AppTheme.stateSuccess),
                          const SizedBox(height: 16),
                          Text('All offline actions acknowledged by server.', style: textTheme.titleMedium),
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
                      return Card(
                        margin: const EdgeInsets.only(bottom: 10),
                        child: ListTile(
                          leading: const Icon(Icons.pending_actions, color: AppTheme.primaryLightViolet),
                          title: Text('Mutation: ${item.mutationType}', style: textTheme.titleMedium),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('ID: ${item.mutationId}', style: const TextStyle(fontSize: 11, fontFamily: 'monospace')),
                              Text('Recorded: ${item.clientTimestamp}', style: textTheme.bodySmall),
                            ],
                          ),
                          trailing: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: AppTheme.stateWarning.withValues(alpha: 0.2),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              item.status,
                              style: const TextStyle(fontSize: 10, color: AppTheme.stateWarning, fontWeight: FontWeight.bold),
                            ),
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
