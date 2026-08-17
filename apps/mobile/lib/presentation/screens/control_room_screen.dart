// CineVault OS — Control Room Curator Screen (Build Unit 8.10)
// Curator dashboard for candidate inspection, evidence breakdown, promote/reject curation, and audit logging

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../providers/control_room_provider.dart';
import '../../domain/entities/control_room.dart';

class ControlRoomScreen extends ConsumerStatefulWidget {
  const ControlRoomScreen({super.key});

  @override
  ConsumerState<ControlRoomScreen> createState() => _ControlRoomScreenState();
}

class _ControlRoomScreenState extends ConsumerState<ControlRoomScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(controlRoomProvider);
    final curatorRoleAsync = ref.watch(curatorRoleProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Control Room Curation'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref.read(controlRoomProvider.notifier).fetchDashboard();
            },
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppTheme.accentGold,
          tabs: const [
            Tab(text: 'Reconciliation Candidates'),
            Tab(text: 'Audit Log History'),
          ],
        ),
      ),
      body: curatorRoleAsync.when(
        data: (isCurator) {
          if (!isCurator) {
            return const Center(
              child: Text(
                'Access Restricted: Curator role required.',
                style: TextStyle(color: Colors.redAccent, fontSize: 16),
              ),
            );
          }

          if (state.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (state.errorMessage != null && state.summary == null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    'Error loading dashboard: ${state.errorMessage}',
                    style: const TextStyle(color: Colors.redAccent),
                  ),
                  const SizedBox(height: 12),
                  ElevatedButton(
                    onPressed: () => ref.read(controlRoomProvider.notifier).fetchDashboard(),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          return Column(
            children: [
              if (state.summary != null) _buildSummaryHeader(state.summary!),
              Expanded(
                child: TabBarView(
                  controller: _tabController,
                  children: [
                    _buildCandidatesTab(state.candidates),
                    _buildAuditLogsTab(state.auditLogs),
                  ],
                ),
              ),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Role authorization error: $err')),
      ),
    );
  }

  Widget _buildSummaryHeader(ControlRoomSummaryEntity summary) {
    return Container(
      padding: const EdgeInsets.all(12.0),
      color: AppTheme.cardElevated,
      child: Row(
        children: [
          Expanded(
            child: _buildMetricTile(
              'Candidates',
              '${summary.pendingCandidates}',
              Colors.orangeAccent,
            ),
          ),
          Expanded(
            child: _buildMetricTile(
              'AI Proposals',
              '${summary.pendingAiProposals}',
              Colors.cyanAccent,
            ),
          ),
          Expanded(
            child: _buildMetricTile(
              'Quarantine',
              '${summary.pendingQuarantineRecords}',
              Colors.redAccent,
            ),
          ),
          Expanded(
            child: _buildMetricTile(
              'Promoted',
              '${summary.promotedCanonicalRecords}',
              Colors.greenAccent,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricTile(String label, String value, Color color) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          label,
          style: const TextStyle(fontSize: 11, color: Colors.grey),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _buildCandidatesTab(List<ReconciliationCandidateEntity> candidates) {
    if (candidates.isEmpty) {
      return const Center(
        child: Text('No pending reconciliation candidates found.'),
      );
    }

    return ListView.builder(
      itemCount: candidates.length,
      padding: const EdgeInsets.all(12),
      itemBuilder: (context, index) {
        final candidate = candidates[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Chip(
                      label: Text(
                        candidate.sourceProvider,
                        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                      ),
                      backgroundColor: Colors.blueGrey.shade800,
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: candidate.matchConfidence >= 0.8
                            ? Colors.green.shade900
                            : Colors.amber.shade900,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        'Confidence: ${(candidate.matchConfidence * 100).toStringAsFixed(1)}%',
                        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'Candidate ID: ${candidate.candidateId}',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                ),
                const SizedBox(height: 4),
                Text(
                  'Suggested Action: ${candidate.suggestedAction} | Status: ${candidate.status}',
                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                ),
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    OutlinedButton(
                      onPressed: () => _showEvidenceModal(candidate.candidateId),
                      child: const Text('Evidence'),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.green.shade800),
                      onPressed: () => _showPromoteDialog(candidate.candidateId),
                      child: const Text('Promote'),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.red.shade800),
                      onPressed: () => _showRejectDialog(candidate.candidateId),
                      child: const Text('Reject'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildAuditLogsTab(List<AuditLogEntryEntity> logs) {
    if (logs.isEmpty) {
      return const Center(child: Text('No audit logs recorded.'));
    }

    return ListView.builder(
      itemCount: logs.length,
      padding: const EdgeInsets.all(12),
      itemBuilder: (context, index) {
        final log = logs[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: ListTile(
            title: Text(
              log.eventType,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
            ),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Actor: ${log.actorId} | Target: ${log.targetId ?? "N/A"}'),
                Text(
                  'Hash: ${log.integrityHash.length > 16 ? log.integrityHash.substring(0, 16) : log.integrityHash}...',
                  style: const TextStyle(fontFamily: 'monospace', fontSize: 10, color: Colors.amberAccent),
                ),
              ],
            ),
            trailing: Text(
              log.timestamp.length > 10 ? log.timestamp.substring(0, 10) : log.timestamp,
              style: const TextStyle(fontSize: 11, color: Colors.grey),
            ),
          ),
        );
      },
    );
  }

  void _showEvidenceModal(String candidateId) {
    ref.read(controlRoomProvider.notifier).loadCandidateDetail(candidateId);
    showModalBottomSheet(
      context: context,
      backgroundColor: AppTheme.cardElevated,
      builder: (context) {
        return Consumer(
          builder: (context, ref, child) {
            final detail = ref.watch(controlRoomProvider).selectedCandidateDetail;
            if (detail == null) {
              return const SizedBox(
                height: 200,
                child: Center(child: CircularProgressIndicator()),
              );
            }
            return Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    'Evidence Breakdown: ${detail.candidateId}',
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  const Divider(),
                  Text('Provider: ${detail.providerName} (External ID: ${detail.externalId})'),
                  Text('Rule Executed: ${detail.matchRuleId}'),
                  Text('Match Score: ${(detail.matchConfidence * 100).toStringAsFixed(1)}%'),
                  const SizedBox(height: 8),
                  const Text('Payload Provenance:', style: TextStyle(fontWeight: FontWeight.bold)),
                  Text(
                    detail.evidenceSummary.toString(),
                    style: const TextStyle(fontSize: 11, fontFamily: 'monospace', color: Colors.grey),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  void _showPromoteDialog(String candidateId) {
    final controller = TextEditingController(text: 'Approved human curation verification');
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Promote Candidate'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('Promote candidate to CAT-1 Canonical Platform Data?'),
              const SizedBox(height: 12),
              TextField(
                controller: controller,
                decoration: const InputDecoration(
                  labelText: 'Curator Rationale',
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
              onPressed: () async {
                final nav = Navigator.of(context);
                final messenger = ScaffoldMessenger.of(context);
                final ok = await ref.read(controlRoomProvider.notifier).promoteCandidate(candidateId, controller.text);
                nav.pop();
                if (ok && mounted) {
                  messenger.showSnackBar(
                    const SnackBar(content: Text('Candidate promoted successfully!')),
                  );
                }
              },
              child: const Text('Confirm Promote'),
            ),
          ],
        );
      },
    );
  }

  void _showRejectDialog(String candidateId) {
    final controller = TextEditingController(text: 'Rejected by curator inspection');
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Reject Candidate'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('Reject candidate and log audit entry?'),
              const SizedBox(height: 12),
              TextField(
                controller: controller,
                decoration: const InputDecoration(
                  labelText: 'Curator Rationale',
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
              onPressed: () async {
                final nav = Navigator.of(context);
                final messenger = ScaffoldMessenger.of(context);
                final ok = await ref.read(controlRoomProvider.notifier).rejectCandidate(candidateId, controller.text);
                nav.pop();
                if (ok && mounted) {
                  messenger.showSnackBar(
                    const SnackBar(content: Text('Candidate rejected.')),
                  );
                }
              },
              child: const Text('Confirm Reject'),
            ),
          ],
        );
      },
    );
  }
}
