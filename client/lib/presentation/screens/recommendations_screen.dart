// CineVault OS — Recommendations Screen (8.7)
// Personalized recommendations with modes (tonight, weekend, deep_dive) and grounded explanations

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../providers/recommendation_provider.dart';
import 'title_detail_screen.dart';

class RecommendationsScreen extends ConsumerWidget {
  const RecommendationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recState = ref.watch(recommendationProvider);
    final textTheme = Theme.of(context).textTheme;

    final modes = [
      {'id': 'tonight', 'label': 'Tonight'},
      {'id': 'weekend', 'label': 'Weekend Binge'},
      {'id': 'deep_dive', 'label': 'Deep Dive'},
      {'id': 'because_you_liked', 'label': 'Based on Taste'},
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Recommendations (8.7 Engine)'),
      ),
      body: Column(
        children: [
          // Mode Tabs
          Container(
            color: AppTheme.cardSurface,
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Row(
                children: modes.map((m) {
                  final isSelected = recState.activeMode == m['id'];
                  return Padding(
                    padding: const EdgeInsets.only(right: 8.0),
                    child: ChoiceChip(
                      label: Text(m['label']!),
                      selected: isSelected,
                      onSelected: (_) => ref.read(recommendationProvider.notifier).fetchRecommendations(m['id']!),
                      selectedColor: AppTheme.primaryViolet,
                    ),
                  );
                }).toList(),
              ),
            ),
          ),

          // Main List
          Expanded(
            child: recState.isLoading
                ? const Center(child: CircularProgressIndicator(semanticsLabel: 'Generating personalized recommendations'))
                : recState.errorMessage != null
                    ? Center(child: Text(recState.errorMessage!, style: textTheme.bodyLarge))
                    : recState.items.isEmpty
                        ? Center(child: Text('No recommendations generated for this mode.', style: textTheme.bodyMedium))
                        : ListView.builder(
                            padding: const EdgeInsets.all(16),
                            itemCount: recState.items.length,
                            itemBuilder: (context, index) {
                              final item = recState.items[index];
                              final scorePct = (item.recommendationScore * 100).toStringAsFixed(0);

                              return Card(
                                margin: const EdgeInsets.only(bottom: 12),
                                child: Padding(
                                  padding: const EdgeInsets.all(12.0),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        children: [
                                          Expanded(
                                            child: Text(item.titleName, style: textTheme.titleMedium),
                                          ),
                                          Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                            decoration: BoxDecoration(
                                              color: AppTheme.secondaryCyan.withOpacity(0.2),
                                              borderRadius: BorderRadius.circular(6),
                                            ),
                                            child: Text(
                                              '$scorePct% Match',
                                              style: const TextStyle(
                                                color: AppTheme.secondaryCyan,
                                                fontWeight: FontWeight.bold,
                                                fontSize: 12,
                                              ),
                                            ),
                                          ),
                                        ],
                                      ),
                                      const SizedBox(height: 8),
                                      // Grounded Explanation Box
                                      Container(
                                        padding: const EdgeInsets.all(10),
                                        decoration: BoxDecoration(
                                          color: AppTheme.cardElevated,
                                          borderRadius: BorderRadius.circular(8),
                                        ),
                                        child: Row(
                                          children: [
                                            const Icon(Icons.psychology_outlined, color: AppTheme.accentGold, size: 20),
                                            const SizedBox(width: 8),
                                            Expanded(
                                              child: Text(
                                                item.groundedExplanation.textualExplanation,
                                                style: textTheme.bodyMedium,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                      const SizedBox(height: 8),
                                      Align(
                                        alignment: Alignment.centerRight,
                                        child: TextButton.icon(
                                          icon: const Icon(Icons.arrow_forward),
                                          label: const Text('View Title'),
                                          onPressed: () {
                                            Navigator.push(
                                              context,
                                              MaterialPageRoute(
                                                builder: (_) => TitleDetailScreen(titleId: item.titleId),
                                              ),
                                            );
                                          },
                                        ),
                                      ),
                                    ],
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
