// CineVault OS — Settings & Profile Screen (Part 3: Profile/Settings)
// Account info, referral stats shortcut, and the multi-format data-export
// hub (mirrors apps/web/src/app/settings/page.tsx / lib/api/import.ts's
// downloadExport). Sign-out already lives on Library's Analytics tab — kept
// here too since Settings is the more conventional place to look for it.

import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';
import '../../core/theme/app_theme.dart';
import '../providers/auth_provider.dart';
import '../providers/personal_provider.dart';
import '../widgets/glass/glass.dart';
import 'invite_screen.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  String? _exportingFormat;
  String? _exportError;

  static const _formats = <_ExportFormat>[
    _ExportFormat(id: 'json', label: 'JSON', extension: 'json', icon: Icons.data_object),
    _ExportFormat(id: 'csv', label: 'CSV', extension: 'zip', icon: Icons.table_chart_outlined),
    _ExportFormat(id: 'excel', label: 'Excel', extension: 'xlsx', icon: Icons.grid_on),
    _ExportFormat(id: 'markdown', label: 'Markdown', extension: 'md', icon: Icons.article_outlined),
  ];

  Future<void> _export(_ExportFormat format) async {
    setState(() {
      _exportingFormat = format.id;
      _exportError = null;
    });
    try {
      final bytes = await ref.read(personalRemoteDatasourceProvider).exportPersonalData(format: format.id);
      final dir = await getApplicationDocumentsDirectory();
      final dateStamp = DateTime.now().toIso8601String().split('T').first;
      final file = File('${dir.path}/cinevault_export_$dateStamp.${format.extension}');
      await file.writeAsBytes(bytes);

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Saved ${format.label} export to ${file.path}')),
      );
    } catch (e) {
      setState(() => _exportError = 'Export failed: $e');
    } finally {
      if (mounted) setState(() => _exportingFormat = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: const GlassAppBar(title: Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          GlassAppBar.contentSpacer(context),
          const SizedBox(height: 8),

          // Account section
          GlassCard(
            child: Row(
              children: [
                CircleAvatar(
                  radius: 26,
                  backgroundColor: AppTheme.accentGold.withValues(alpha: 0.2),
                  child: const Icon(Icons.person, color: AppTheme.accentGold, size: 28),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        authState.session?.email ?? 'CineVault User',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Roles: ${authState.session?.roles.join(", ") ?? "AuthenticatedUser"}',
                        style: const TextStyle(fontSize: 12, color: AppTheme.textMuted),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Invite / referrals shortcut
          GlassCard(
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const InviteScreen()),
            ),
            child: const Row(
              children: [
                Icon(Icons.person_add_outlined, color: AppTheme.secondaryCyan),
                SizedBox(width: 12),
                Expanded(child: Text('Invite a Friend & Referral Stats')),
                Icon(Icons.chevron_right, color: AppTheme.textMuted),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // Export hub
          Text('Export Your Data', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 4),
          const Text(
            'Download your watch history, ratings, and library in a portable format.',
            style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
          ),
          const SizedBox(height: 12),
          if (_exportError != null) ...[
            GlassCard(
              tintColor: AppTheme.stateError,
              child: Row(
                children: [
                  const Icon(Icons.error_outline, color: AppTheme.stateError),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(_exportError!, style: const TextStyle(color: AppTheme.stateError)),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
          ],
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: _formats.map((format) {
              final isExporting = _exportingFormat == format.id;
              return GlassCard(
                onTap: isExporting ? null : () => _export(format),
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (isExporting)
                      const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    else
                      Icon(format.icon, color: AppTheme.primaryLightViolet),
                    const SizedBox(width: 10),
                    Text(format.label),
                  ],
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 24),

          ElevatedButton.icon(
            onPressed: () {
              ref.read(authProvider.notifier).logout();
            },
            icon: const Icon(Icons.logout),
            label: const Text('SIGN OUT'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red.shade900.withValues(alpha: 0.8),
              foregroundColor: Colors.white,
            ),
          ),
        ],
      ),
    );
  }
}

class _ExportFormat {
  final String id;
  final String label;
  final String extension;
  final IconData icon;

  const _ExportFormat({
    required this.id,
    required this.label,
    required this.extension,
    required this.icon,
  });
}
