// CineVault OS — Collection Detail Screen (Part 3.5)
// Shows the titles saved inside one user collection; supports removing items.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../providers/collections_provider.dart';
import '../widgets/glass/glass.dart';

class CollectionDetailScreen extends ConsumerWidget {
  const CollectionDetailScreen({
    super.key,
    required this.collectionId,
    this.collectionName,
  });

  final String collectionId;
  final String? collectionName;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final detailAsync = ref.watch(collectionDetailProvider(collectionId));

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: GlassAppBar(title: Text(collectionName ?? 'Collection')),
      body: Column(
        children: [
          GlassAppBar.contentSpacer(context),
          Expanded(
            child: detailAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (err, _) => Center(
                child: GlassCard(
                  margin: const EdgeInsets.all(24),
                  child: Text(
                    'Failed to load collection: $err',
                    style: const TextStyle(color: Colors.grey),
                  ),
                ),
              ),
              data: (detail) {
                final items = detail.items;
                if (items.isEmpty) {
                  return const Center(
                    child: GlassCard(
                      margin: EdgeInsets.all(24),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.movie_filter_outlined, size: 64, color: Colors.grey),
                          SizedBox(height: 12),
                          Text('No titles in this collection yet.', style: TextStyle(color: Colors.grey)),
                        ],
                      ),
                    ),
                  );
                }
                return ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: items.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 8),
                  itemBuilder: (context, index) {
                    final item = items[index];
                    return GlassCard(
                      padding: EdgeInsets.zero,
                      child: ListTile(
                        leading: Container(
                          width: 40,
                          height: 56,
                          decoration: BoxDecoration(
                            color: AppTheme.cardElevated,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          clipBehavior: Clip.antiAlias,
                          child: item.posterUrl != null && item.posterUrl!.isNotEmpty
                              ? Image.network(
                                  item.posterUrl!,
                                  fit: BoxFit.cover,
                                  errorBuilder: (context, error, stackTrace) => Icon(
                                    item.contentType == 'MOVIE' ? Icons.movie : Icons.tv,
                                    color: AppTheme.primaryViolet,
                                    size: 24,
                                  ),
                                )
                              : Icon(
                                  item.contentType == 'MOVIE' ? Icons.movie : Icons.tv,
                                  color: AppTheme.primaryViolet,
                                  size: 24,
                                ),
                        ),
                        title: Text(item.canonicalTitle),
                        subtitle: Text(item.productionYear?.toString() ?? 'N/A'),
                        trailing: IconButton(
                          icon: const Icon(Icons.remove_circle_outline),
                          tooltip: 'Remove from collection',
                          onPressed: () => _removeItem(context, ref, item.titleId),
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _removeItem(BuildContext context, WidgetRef ref, String titleId) async {
    try {
      await ref.read(collectionsRepositoryProvider).removeCollectionItem(
            collectionId: collectionId,
            titleId: titleId,
          );
      ref.invalidate(collectionDetailProvider(collectionId));
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to remove title: $e')),
        );
      }
    }
  }
}
