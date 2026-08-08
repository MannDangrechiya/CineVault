// CineVault OS — AI Assistant Screen (8.8)
// Conversational natural language query UI with prompt sanitization and title citations

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../providers/ai_assistant_provider.dart';
import 'title_detail_screen.dart';

class AiAssistantScreen extends ConsumerStatefulWidget {
  const AiAssistantScreen({super.key});

  @override
  ConsumerState<AiAssistantScreen> createState() => _AiAssistantScreenState();
}

class _AiAssistantScreenState extends ConsumerState<AiAssistantScreen> {
  final TextEditingController _queryController = TextEditingController();

  void _sendQuery() {
    final text = _queryController.text;
    if (text.trim().isEmpty) return;

    ref.read(aiAssistantProvider.notifier).submitQuery(text);
    _queryController.clear();
  }

  @override
  Widget build(BuildContext context) {
    final aiState = ref.watch(aiAssistantProvider);
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Assistant (8.8 Backend)'),
      ),
      body: Column(
        children: [
          // Banner
          Container(
            padding: const EdgeInsets.all(12),
            color: AppTheme.primaryViolet.withValues(alpha: 0.15),
            child: const Row(
              children: [
                Icon(Icons.auto_awesome, color: AppTheme.primaryLightViolet),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Ask natural language queries. All AI responses are grounded via CineVault backend governance.',
                    style: TextStyle(fontSize: 12, color: AppTheme.textPrimary),
                  ),
                ),
              ],
            ),
          ),

          // Messages List
          Expanded(
            child: aiState.chatHistory.isEmpty
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24.0),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.forum_outlined, size: 64, color: AppTheme.textMuted),
                          const SizedBox(height: 16),
                          Text('Try asking:', style: textTheme.titleMedium),
                          const SizedBox(height: 8),
                          const Text('"Find me sci-fi movies from 2024 available on streaming"', style: TextStyle(color: AppTheme.textMuted)),
                          const Text('"Suggest a dark comedy for tonight under 100 minutes"', style: TextStyle(color: AppTheme.textMuted)),
                        ],
                      ),
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: aiState.chatHistory.length,
                    itemBuilder: (context, index) {
                      final item = aiState.chatHistory[index];
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            // User Query Bubble
                            Align(
                              alignment: Alignment.centerRight,
                              child: Container(
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: AppTheme.primaryViolet,
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Text(item.rawQuery, style: const TextStyle(color: Colors.white)),
                              ),
                            ),
                            const SizedBox(height: 8),

                            // Assistant Response Bubble
                            Align(
                              alignment: Alignment.centerLeft,
                              child: Container(
                                padding: const EdgeInsets.all(14),
                                decoration: BoxDecoration(
                                  color: AppTheme.cardSurface,
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(color: AppTheme.borderSubtle),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      children: [
                                        const Icon(Icons.auto_awesome, color: AppTheme.secondaryCyan, size: 18),
                                        const SizedBox(width: 6),
                                        Text('Intent: ${item.detectedIntent.intentType}', style: textTheme.bodySmall),
                                        const Spacer(),
                                        Text('${(item.confidenceScore * 100).toInt()}% confidence', style: textTheme.bodySmall),
                                      ],
                                    ),
                                    const Divider(height: 16, color: AppTheme.borderSubtle),
                                    Text(item.responseText, style: textTheme.bodyLarge),
                                    if (item.titleCitations.isNotEmpty) ...[
                                      const SizedBox(height: 12),
                                      Text('Citations:', style: textTheme.titleMedium),
                                      Wrap(
                                        spacing: 6,
                                        children: item.titleCitations.map((titleId) {
                                          return ActionChip(
                                            avatar: const Icon(Icons.movie, size: 14),
                                            label: Text('Title $titleId'),
                                            onPressed: () {
                                              Navigator.push(
                                                context,
                                                MaterialPageRoute(
                                                  builder: (_) => TitleDetailScreen(titleId: titleId),
                                                ),
                                              );
                                            },
                                          );
                                        }).toList(),
                                      ),
                                    ],
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
          ),

          if (aiState.isProcessing)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 8.0),
              child: LinearProgressIndicator(semanticsLabel: 'Processing AI Query'),
            ),

          // Input Bar
          Padding(
            padding: const EdgeInsets.all(12.0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _queryController,
                    decoration: const InputDecoration(
                      hintText: 'Type your movie query or request...',
                    ),
                    onSubmitted: (_) => _sendQuery(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  icon: const Icon(Icons.send),
                  style: IconButton.styleFrom(backgroundColor: AppTheme.primaryViolet),
                  onPressed: _sendQuery,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
