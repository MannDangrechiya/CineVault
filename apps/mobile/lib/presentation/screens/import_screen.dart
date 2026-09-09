// CineVault OS — Import Watch History Screen (Part 3.9)
// Self-contained 3-step wizard: pick a file (CSV/JSON/plain-text) -> preview
// match confidence -> apply the import. Uses ImportTextParser for local
// parsing and importRemoteDatasourceProvider for the preview/apply calls.

import 'dart:convert';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_theme.dart';
import '../../core/utils/import_text_parser.dart';
import '../../domain/entities/import_data.dart';
import '../providers/import_provider.dart';
import '../widgets/glass/glass.dart';

const int _stepPickFile = 0;
const int _stepPreview = 1;
const int _stepResult = 2;

class ImportScreen extends ConsumerStatefulWidget {
  const ImportScreen({super.key});

  @override
  ConsumerState<ImportScreen> createState() => _ImportScreenState();
}

class _ImportScreenState extends ConsumerState<ImportScreen> {
  int _step = _stepPickFile;

  List<ImportItem> _parsedItems = const [];
  ImportPreviewResult? _previewResult;
  ImportApplyResult? _applyResult;

  bool _isBusy = false;
  String? _errorMessage;

  Future<void> _pickFile() async {
    setState(() => _errorMessage = null);

    final FilePickerResult? result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['csv', 'json', 'txt'],
      withData: true,
    );
    if (result == null || result.files.isEmpty) return;

    final bytes = result.files.single.bytes;
    if (bytes == null) {
      setState(() => _errorMessage = 'Could not read the selected file.');
      return;
    }

    final text = utf8.decode(bytes, allowMalformed: true);
    final items = ImportTextParser.parse(text);

    if (items.isEmpty) {
      setState(() {
        _parsedItems = const [];
        _errorMessage = "Couldn't recognize any titles in that file.";
      });
      return;
    }

    setState(() {
      _parsedItems = items;
      _errorMessage = null;
    });
  }

  Future<void> _previewImport() async {
    setState(() {
      _isBusy = true;
      _errorMessage = null;
    });

    try {
      final datasource = ref.read(importRemoteDatasourceProvider);
      final result = await datasource.previewImport(_parsedItems);
      if (!mounted) return;
      setState(() {
        _previewResult = result;
        _isBusy = false;
        _step = _stepPreview;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isBusy = false;
        _errorMessage = 'Preview failed: $e';
      });
    }
  }

  Future<void> _applyImport() async {
    setState(() {
      _isBusy = true;
      _errorMessage = null;
    });

    try {
      final datasource = ref.read(importRemoteDatasourceProvider);
      final result = await datasource.applyImport(items: _parsedItems);
      if (!mounted) return;
      setState(() {
        _applyResult = result;
        _isBusy = false;
        _step = _stepResult;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isBusy = false;
        _errorMessage = 'Apply failed: $e';
      });
    }
  }

  void _startOver() {
    setState(() {
      _step = _stepPickFile;
      _parsedItems = const [];
      _previewResult = null;
      _applyResult = null;
      _errorMessage = null;
      _isBusy = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: const GlassAppBar(title: Text('Import Watch History')),
      body: Column(
        children: [
          GlassAppBar.contentSpacer(context),
          Expanded(child: _buildStep(context)),
        ],
      ),
    );
  }

  Widget _buildStep(BuildContext context) {
    switch (_step) {
      case _stepPreview:
        return _PreviewStep(
          previewResult: _previewResult!,
          isBusy: _isBusy,
          errorMessage: _errorMessage,
          onApply: _applyImport,
          onStartOver: _startOver,
        );
      case _stepResult:
        return _ResultStep(
          applyResult: _applyResult!,
          onDone: () => Navigator.pop(context),
          onImportAnother: _startOver,
        );
      case _stepPickFile:
      default:
        return _PickFileStep(
          parsedItemCount: _parsedItems.length,
          isBusy: _isBusy,
          errorMessage: _errorMessage,
          onPickFile: _pickFile,
          onPreview: _previewImport,
        );
    }
  }
}

class _PickFileStep extends StatelessWidget {
  const _PickFileStep({
    required this.parsedItemCount,
    required this.isBusy,
    required this.errorMessage,
    required this.onPickFile,
    required this.onPreview,
  });

  final int parsedItemCount;
  final bool isBusy;
  final String? errorMessage;
  final VoidCallback onPickFile;
  final VoidCallback onPreview;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          GlassCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(
                      Icons.file_upload_outlined,
                      color: AppTheme.primaryViolet,
                      size: 28,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Import Your Watch History',
                        style: textTheme.titleMedium,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  'Import your watch history from Letterboxd (CSV), a JSON '
                  'export, or a plain-text list.',
                  style: textTheme.bodyMedium,
                ),
                const SizedBox(height: 16),
                ElevatedButton.icon(
                  icon: const Icon(Icons.folder_open),
                  label: const Text('Choose File'),
                  onPressed: isBusy ? null : onPickFile,
                ),
              ],
            ),
          ),
          if (errorMessage != null) ...[
            const SizedBox(height: 12),
            _ErrorBanner(message: errorMessage!),
          ],
          if (parsedItemCount > 0) ...[
            const SizedBox(height: 12),
            GlassCard(
              tintColor: AppTheme.stateSuccess,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    children: [
                      const Icon(
                        Icons.check_circle_outline,
                        color: AppTheme.stateSuccess,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Found $parsedItemCount items',
                          style: textTheme.titleSmall,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  ElevatedButton.icon(
                    icon: isBusy
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(Icons.visibility_outlined),
                    label: Text(isBusy ? 'Loading Preview...' : 'Preview Import'),
                    onPressed: isBusy ? null : onPreview,
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _PreviewStep extends StatelessWidget {
  const _PreviewStep({
    required this.previewResult,
    required this.isBusy,
    required this.errorMessage,
    required this.onApply,
    required this.onStartOver,
  });

  final ImportPreviewResult previewResult;
  final bool isBusy;
  final String? errorMessage;
  final VoidCallback onApply;
  final VoidCallback onStartOver;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: _StatTilesRow(previewResult: previewResult),
        ),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            itemCount: previewResult.itemVerdicts.length,
            itemBuilder: (context, index) {
              return _VerdictRow(verdict: previewResult.itemVerdicts[index]);
            },
          ),
        ),
        if (errorMessage != null)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
            child: _ErrorBanner(message: errorMessage!),
          ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: isBusy ? null : onStartOver,
                  child: const Text('Start Over'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                flex: 2,
                child: ElevatedButton.icon(
                  icon: isBusy
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.cloud_upload_outlined),
                  label: Text(isBusy ? 'Applying...' : 'Apply Import'),
                  onPressed: isBusy ? null : onApply,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _StatTilesRow extends StatelessWidget {
  const _StatTilesRow({required this.previewResult});

  final ImportPreviewResult previewResult;

  @override
  Widget build(BuildContext context) {
    final stats = <(String, int, Color)>[
      ('Total', previewResult.totalItems, AppTheme.primaryLightViolet),
      ('Matched', previewResult.matchedTitles, AppTheme.stateSuccess),
      ('Probable', previewResult.probableMatches, AppTheme.stateWarning),
      ('Review', previewResult.reviewRequired, AppTheme.secondaryCyan),
      ('Unmatched', previewResult.unmatchedTitles, AppTheme.stateError),
      ('Conflicts', previewResult.conflictsCount, AppTheme.accentGold),
    ];

    return SizedBox(
      height: 72,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: stats.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final (label, count, color) = stats[index];
          return GlassCard(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  '$count',
                  style: TextStyle(
                    color: color,
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  label,
                  style: const TextStyle(color: AppTheme.textMuted, fontSize: 11),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _VerdictRow extends StatelessWidget {
  const _VerdictRow({required this.verdict});

  final ImportItemVerdictResult verdict;

  static const _verdictLabels = {
    ImportVerdict.exactMatch: 'Exact',
    ImportVerdict.probableMatch: 'Probable',
    ImportVerdict.reviewRequired: 'Review',
    ImportVerdict.unmatched: 'Unmatched',
  };

  static const _verdictTints = {
    ImportVerdict.exactMatch: AppTheme.stateSuccess,
    ImportVerdict.probableMatch: AppTheme.stateWarning,
    ImportVerdict.reviewRequired: AppTheme.secondaryCyan,
    ImportVerdict.unmatched: AppTheme.stateError,
  };

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final topCandidate = verdict.candidates.isNotEmpty ? verdict.candidates.first : null;

    return GlassCard(
      margin: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  verdict.productionYear != null
                      ? '${verdict.canonicalTitle} (${verdict.productionYear})'
                      : verdict.canonicalTitle,
                  style: textTheme.titleSmall,
                  overflow: TextOverflow.ellipsis,
                ),
                if (topCandidate != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    'Best match: ${topCandidate.canonicalTitle} '
                    '(${(topCandidate.confidence * 100).toStringAsFixed(0)}%)',
                    style: const TextStyle(color: AppTheme.textMuted, fontSize: 12),
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(width: 8),
          GlassBadge(
            label: _verdictLabels[verdict.verdict] ?? 'Unmatched',
            tint: _verdictTints[verdict.verdict] ?? AppTheme.stateError,
          ),
        ],
      ),
    );
  }
}

class _ResultStep extends StatelessWidget {
  const _ResultStep({
    required this.applyResult,
    required this.onDone,
    required this.onImportAnother,
  });

  final ImportApplyResult applyResult;
  final VoidCallback onDone;
  final VoidCallback onImportAnother;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: GlassCard(
          tintColor: AppTheme.stateSuccess,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(
                Icons.check_circle_outline,
                color: AppTheme.stateSuccess,
                size: 56,
              ),
              const SizedBox(height: 16),
              Text(
                'Imported ${applyResult.appliedCount} titles',
                style: textTheme.titleLarge,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 4),
              Text(
                '${applyResult.conflictsResolved} conflicts resolved',
                style: const TextStyle(color: AppTheme.textMuted),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(onPressed: onDone, child: const Text('Done')),
              ),
              const SizedBox(height: 8),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  onPressed: onImportAnother,
                  child: const Text('Import Another File'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      tintColor: AppTheme.stateError,
      child: Row(
        children: [
          const Icon(Icons.error_outline, color: AppTheme.stateError),
          const SizedBox(width: 8),
          Expanded(
            child: Text(message, style: const TextStyle(color: AppTheme.stateError)),
          ),
        ],
      ),
    );
  }
}
