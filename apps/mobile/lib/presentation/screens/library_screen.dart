// CineVault OS — Personal Library & Profile Screen (Phase 20)
// Watchlist, completed status, watch history timeline, ratings, private notes, collections, and stats

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../domain/entities/personal.dart';
import '../../domain/entities/social.dart';
import '../providers/auth_provider.dart';
import '../providers/collections_provider.dart';
import '../providers/personal_provider.dart';
import '../providers/social_provider.dart';
import '../providers/sync_provider.dart' show appDatabaseProvider;
import '../../data/repositories/personal_offline_repository.dart';
import '../widgets/glass/glass.dart';
import 'collection_detail_screen.dart';

final personalOfflineRepositoryProvider = Provider<PersonalOfflineRepository>((ref) {
  final db = ref.watch(appDatabaseProvider);
  return PersonalOfflineRepository(db);
});

class LibraryScreen extends ConsumerStatefulWidget {
  const LibraryScreen({super.key});

  @override
  ConsumerState<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends ConsumerState<LibraryScreen> {
  int _selectedTab = 0;

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final offlineRepo = ref.watch(personalOfflineRepositoryProvider);

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: const GlassAppBar(
        title: Text('My Library'),
      ),
      body: Column(
        children: [
          GlassAppBar.contentSpacer(context),
          // Segmented Tab Switcher Bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: Theme.of(context).cardColor,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildTabButton(0, 'Watchlist', Icons.bookmark_outline),
                _buildTabButton(1, 'History', Icons.history_rounded),
                _buildTabButton(2, 'Ratings', Icons.star_outline_rounded),
                _buildTabButton(3, 'Analytics', Icons.analytics_outlined),
                _buildTabButton(4, 'Collections', Icons.collections_bookmark_outlined),
              ],
            ),
          ),
          const Divider(height: 1),

          // Tab Content
          Expanded(
            child: _buildTabBody(_selectedTab, authState, offlineRepo),
          ),
        ],
      ),
      floatingActionButton: _selectedTab == 4
          ? FloatingActionButton(
              onPressed: _showCreateCollectionDialog,
              tooltip: 'New collection',
              child: const Icon(Icons.add),
            )
          : null,
    );
  }

  Widget _buildTabButton(int index, String label, IconData icon) {
    final isSelected = _selectedTab == index;
    return InkWell(
      onTap: () {
        setState(() {
          _selectedTab = index;
        });
      },
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: isSelected ? AppTheme.accentGold : Colors.grey, size: 22),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                color: isSelected ? AppTheme.accentGold : Colors.grey,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                fontSize: 12,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTabBody(int tabIndex, AuthState authState, PersonalOfflineRepository offlineRepo) {
    switch (tabIndex) {
      case 0:
        // Watchlist & Favorites Tab
        return FutureBuilder(
          future: offlineRepo.getOfflineFavorites(),
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            final favs = snapshot.data ?? [];
            if (favs.isEmpty) {
              return const Center(
                child: GlassCard(
                  margin: EdgeInsets.all(24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.bookmark_border_rounded, size: 64, color: Colors.grey),
                      SizedBox(height: 12),
                      Text('No titles in your watchlist or favorites yet.', style: TextStyle(color: Colors.grey)),
                    ],
                  ),
                ),
              );
            }
            return ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: favs.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                final item = favs[index];
                return GlassCard(
                  padding: EdgeInsets.zero,
                  child: ListTile(
                    leading: const Icon(Icons.movie, color: AppTheme.accentGold),
                    title: Text('Title: ${item.titleId.length > 8 ? item.titleId.substring(0, 8) : item.titleId}...'),
                    subtitle: Text('Status: ${item.derivedStatus}'),
                    trailing: item.isFavorite
                        ? const Icon(Icons.star, color: AppTheme.accentGold)
                        : null,
                  ),
                );
              },
            );
          },
        );

      case 1:
        // Watch History Timeline
        return FutureBuilder(
          future: offlineRepo.getOfflineWatchHistory(),
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            final history = snapshot.data ?? [];
            if (history.isEmpty) {
              return const Center(
                child: GlassCard(
                  margin: EdgeInsets.all(24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.history, size: 64, color: Colors.grey),
                      SizedBox(height: 12),
                      Text('No watch events recorded yet.', style: TextStyle(color: Colors.grey)),
                    ],
                  ),
                ),
              );
            }
            return ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: history.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                final event = history[index];
                return GlassCard(
                  padding: EdgeInsets.zero,
                  child: ListTile(
                    leading: const Icon(Icons.check_circle_outline, color: Colors.greenAccent),
                    title: Text('Watched: ${event.titleId.length > 8 ? event.titleId.substring(0, 8) : event.titleId}...'),
                    subtitle: Text('Progress: ${event.progressPercentage.toInt()}% • Date: ${event.watchedAt.split("T").first}'),
                  ),
                );
              },
            );
          },
        );

      case 2:
        // Ratings Tab
        return FutureBuilder(
          future: offlineRepo.getOfflineRatings(),
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            final ratings = snapshot.data ?? [];
            if (ratings.isEmpty) {
              return const Center(
                child: GlassCard(
                  margin: EdgeInsets.all(24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.star_border, size: 64, color: Colors.grey),
                      SizedBox(height: 12),
                      Text('No ratings submitted yet.', style: TextStyle(color: Colors.grey)),
                    ],
                  ),
                ),
              );
            }
            return ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: ratings.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                final r = ratings[index];
                return GlassCard(
                  padding: EdgeInsets.zero,
                  child: ListTile(
                    leading: const Icon(Icons.stars_rounded, color: AppTheme.accentGold),
                    title: Text('Title: ${r.titleId.length > 8 ? r.titleId.substring(0, 8) : r.titleId}...'),
                    trailing: Text('${r.ratingValue}/10', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  ),
                );
              },
            );
          },
        );

      case 3:
        // Analytics & Profile Tab
        final streakAsync = ref.watch(userStreakProvider);
        final analyticsAsync = ref.watch(personalAnalyticsProvider);
        final badgesAsync = ref.watch(userBadgesProvider);
        return Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              GlassCard(
                padding: const EdgeInsets.all(16.0),
                child: Row(
                  children: [
                    CircleAvatar(
                      radius: 28,
                      backgroundColor: AppTheme.accentGold.withValues(alpha: 0.2),
                      child: const Icon(Icons.person, color: AppTheme.accentGold, size: 32),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            authState.session?.email ?? 'Curator User',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Roles: ${authState.session?.roles.join(", ") ?? "AuthenticatedUser"}',
                            style: const TextStyle(fontSize: 12, color: Colors.grey),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: _buildMetricCard(
                      title: 'Watch Streak',
                      value: _formatStreakValue(streakAsync),
                      icon: Icons.local_fire_department,
                      color: Colors.orangeAccent,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildMetricCard(
                      title: 'Total Hours',
                      value: _formatTotalHoursValue(analyticsAsync),
                      icon: Icons.access_time_filled,
                      color: Colors.lightBlueAccent,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              _buildBadgesSection(badgesAsync),
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

      case 4:
        // Collections Tab
        final collectionsAsync = ref.watch(collectionsListProvider);
        return collectionsAsync.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (err, _) => Center(
            child: GlassCard(
              margin: const EdgeInsets.all(24),
              child: Text('Failed to load collections: $err', style: const TextStyle(color: Colors.grey)),
            ),
          ),
          data: (collections) {
            if (collections.isEmpty) {
              return const Center(
                child: GlassCard(
                  margin: EdgeInsets.all(24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.collections_bookmark_outlined, size: 64, color: Colors.grey),
                      SizedBox(height: 12),
                      Text('No collections yet. Tap + to create one.', style: TextStyle(color: Colors.grey)),
                    ],
                  ),
                ),
              );
            }
            return ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: collections.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                final collection = collections[index];
                return GlassCard(
                  padding: EdgeInsets.zero,
                  child: ListTile(
                    leading: const Icon(Icons.collections_bookmark, color: AppTheme.accentGold),
                    title: Text(collection.name),
                    subtitle: Text('${collection.itemCount} titles'),
                    trailing: IconButton(
                      icon: const Icon(Icons.delete_outline),
                      tooltip: 'Delete collection',
                      onPressed: () => _deleteCollection(collection.id),
                    ),
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => CollectionDetailScreen(
                            collectionId: collection.id,
                            collectionName: collection.name,
                          ),
                        ),
                      );
                    },
                  ),
                );
              },
            );
          },
        );

      default:
        return const SizedBox.shrink();
    }
  }

  Future<void> _deleteCollection(String collectionId) async {
    try {
      await ref.read(collectionsRepositoryProvider).deleteCollection(collectionId);
      ref.invalidate(collectionsListProvider);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to delete collection: $e')),
      );
    }
  }

  Future<void> _showCreateCollectionDialog() async {
    final nameController = TextEditingController();
    final formKey = GlobalKey<FormState>();

    await GlassModalSheet.showDialogPanel(
      context: context,
      builder: (dialogContext) => Padding(
        padding: const EdgeInsets.all(20.0),
        child: Form(
          key: formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'New Collection',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: nameController,
                autofocus: true,
                decoration: const InputDecoration(labelText: 'Collection name'),
                validator: (value) =>
                    (value == null || value.trim().isEmpty) ? 'Name is required' : null,
              ),
              const SizedBox(height: 20),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    onPressed: () => Navigator.pop(dialogContext),
                    child: const Text('Cancel'),
                  ),
                  const SizedBox(width: 8),
                  ElevatedButton(
                    onPressed: () async {
                      if (!(formKey.currentState?.validate() ?? false)) return;
                      try {
                        await ref
                            .read(collectionsRepositoryProvider)
                            .createCollection(name: nameController.text.trim());
                        ref.invalidate(collectionsListProvider);
                        if (dialogContext.mounted) Navigator.pop(dialogContext);
                      } catch (e) {
                        if (dialogContext.mounted) {
                          ScaffoldMessenger.of(dialogContext).showSnackBar(
                            SnackBar(content: Text('Failed to create collection: $e')),
                          );
                        }
                      }
                    },
                    child: const Text('Create'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatStreakValue(AsyncValue<UserStreakEntity> streakAsync) {
    return streakAsync.when(
      data: (streak) => '${streak.currentStreak} Days',
      loading: () => '...',
      error: (_, __) => '—',
    );
  }

  String _formatTotalHoursValue(AsyncValue<PersonalAnalyticsEntity> analyticsAsync) {
    return analyticsAsync.when(
      data: (analytics) => '${analytics.totalWatchHours.toStringAsFixed(1)} hrs',
      loading: () => '...',
      error: (_, __) => '—',
    );
  }

  Widget _buildBadgesSection(AsyncValue<UserBadgesEntity> badgesAsync) {
    return badgesAsync.when(
      data: (userBadges) {
        final earned = userBadges.badges.where((badge) => badge.isEarned).toList();
        return GlassCard(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Badges', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
              const SizedBox(height: 12),
              if (earned.isEmpty)
                const Text(
                  'No badges earned yet.',
                  style: TextStyle(fontSize: 12, color: Colors.grey),
                )
              else
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: earned
                      .map(
                        (badge) => GlassBadge(
                          label: badge.name,
                          tint: AppTheme.accentGold,
                          icon: Icons.emoji_events,
                        ),
                      )
                      .toList(),
                ),
            ],
          ),
        );
      },
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const SizedBox.shrink(),
    );
  }

  Widget _buildMetricCard({
    required String title,
    required String value,
    required IconData icon,
    required Color color,
  }) {
    return GlassCard(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(height: 8),
          Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
          const SizedBox(height: 4),
          Text(title, style: const TextStyle(fontSize: 12, color: Colors.grey)),
        ],
      ),
    );
  }
}
