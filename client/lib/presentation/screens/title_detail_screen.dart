// CineVault OS — Title Detail Screen (8.1, 8.2, 8.6, 8.7)
// Displays canonical title metadata, streaming availability (8.6), similar titles (8.7), and watch event logger (8.2)

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../providers/catalog_provider.dart';
import '../providers/recommendation_provider.dart';
import '../providers/sync_provider.dart';

class TitleDetailScreen extends ConsumerWidget {
  final String titleId;

  const TitleDetailScreen({super.key, required this.titleId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final titleAsync = ref.watch(titleDetailProvider(titleId));
    final availabilityAsync = ref.watch(titleAvailabilityProvider(titleId));
    final similarAsync = ref.watch(similarTitlesProvider(titleId));
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Title Details'),
      ),
      body: titleAsync.when(
        loading: () => const Center(child: CircularProgressIndicator(semanticsLabel: 'Loading title details')),
        error: (err, _) => Center(child: Text('Error loading details: $err', style: textTheme.bodyLarge)),
        data: (title) {
          return SingleChildScrollView(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header Container
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: 110,
                      height: 160,
                      decoration: BoxDecoration(
                        color: AppTheme.cardElevated,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Icon(
                        title.contentType == 'MOVIE' ? Icons.movie : Icons.tv,
                        size: 56,
                        color: AppTheme.primaryLightViolet,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(title.primaryTitle, style: textTheme.headlineMedium),
                          const SizedBox(height: 6),
                          if (title.originalTitle != null)
                            Text('Original: ${title.originalTitle}', style: textTheme.bodySmall),
                          const SizedBox(height: 8),
                          Row(
                            children: [
                              Chip(
                                label: Text(title.contentType),
                                backgroundColor: AppTheme.primaryViolet.withOpacity(0.2),
                              ),
                              const SizedBox(width: 8),
                              if (title.releaseYear != null)
                                Chip(label: Text('${title.releaseYear}')),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),

                // Action Buttons (Watch Log & Rating)
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        icon: const Icon(Icons.bookmark_add),
                        label: const Text('Log Watch Event'),
                        onPressed: () => _showWatchLogDialog(context, ref, title.titleId, title.primaryTitle),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),

                // Synopsis
                Text('Synopsis', style: textTheme.titleLarge),
                const SizedBox(height: 8),
                Text(
                  title.overview ?? 'No overview available for this canonical title.',
                  style: textTheme.bodyLarge,
                ),
                const SizedBox(height: 24),

                // Availability Domain Section (8.6)
                Text('Streaming & Platform Availability (8.6)', style: textTheme.titleLarge),
                const SizedBox(height: 8),
                availabilityAsync.when(
                  loading: () => const LinearProgressIndicator(),
                  error: (_, __) => const Text('Availability data unavailable.', style: TextStyle(color: AppTheme.textMuted)),
                  data: (availabilities) {
                    if (availabilities.isEmpty) {
                      return const Text('No active streaming releases found.', style: TextStyle(color: AppTheme.textMuted));
                    }
                    return Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: availabilities.map((avail) {
                        return Chip(
                          avatar: const Icon(Icons.play_circle_fill, color: AppTheme.secondaryCyan, size: 18),
                          label: Text('${avail.platformName} (${avail.availabilityType})'),
                          backgroundColor: AppTheme.cardElevated,
                        );
                      }).toList(),
                    );
                  },
                ),
                const SizedBox(height: 24),

                // Recommendations / Similar Titles (8.7)
                Text('Similar Titles (8.7 Recommendation Engine)', style: textTheme.titleLarge),
                const SizedBox(height: 8),
                similarAsync.when(
                  loading: () => const LinearProgressIndicator(),
                  error: (_, __) => const Text('Similar titles unavailable.', style: TextStyle(color: AppTheme.textMuted)),
                  data: (similarItems) {
                    if (similarItems.isEmpty) {
                      return const Text('No content-similar candidates generated.', style: TextStyle(color: AppTheme.textMuted));
                    }
                    return Column(
                      children: similarItems.map((sim) {
                        return Card(
                          margin: const EdgeInsets.only(bottom: 8),
                          child: ListTile(
                            leading: const Icon(Icons.movie_outlined, color: AppTheme.primaryLightViolet),
                            title: Text(sim.titleName, style: textTheme.titleMedium),
                            subtitle: Text('Score: ${(sim.recommendationScore * 100).toStringAsFixed(1)}% | ${sim.groundedExplanation.textualExplanation}'),
                            onTap: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (_) => TitleDetailScreen(titleId: sim.titleId),
                                ),
                              );
                            },
                          ),
                        );
                      }).toList(),
                    );
                  },
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  void _showWatchLogDialog(BuildContext context, WidgetRef ref, String titleId, String titleName) {
    String watchMode = 'STREAMING';
    final notesController = TextEditingController();

    showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          title: Text('Log Watch Event for $titleName'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<String>(
                value: watchMode,
                decoration: const InputDecoration(labelText: 'Watch Environment'),
                items: const [
                  DropdownMenuItem(value: 'STREAMING', child: Text('Streaming')),
                  DropdownMenuItem(value: 'THEATER', child: Text('Theater')),
                  DropdownMenuItem(value: 'HOME_MEDIA', child: Text('Physical Media')),
                ],
                onChanged: (val) => watchMode = val ?? 'STREAMING',
              ),
              const SizedBox(height: 12),
              TextField(
                controller: notesController,
                decoration: const InputDecoration(labelText: 'Personal Notes (Optional)'),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () {
                ref.read(syncProvider.notifier).queueAndSync(
                  mutationType: 'CREATE_WATCH_EVENT',
                  payload: {
                    'title_id': titleId,
                    'watch_mode': watchMode,
                    'notes': notesController.text.isNotEmpty ? notesController.text : null,
                  },
                );
                Navigator.pop(ctx);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Watch event queued in local outbox (ADR-004)')),
                );
              },
              child: const Text('Save Event'),
            ),
          ],
        );
      },
    );
  }
}
