// CineVault OS — Personal Library & Profile Screen (Phase 20)
// Watchlist, completed status, watch history timeline, ratings, private notes, collections, and stats

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../providers/auth_provider.dart';
import '../providers/sync_provider.dart' show appDatabaseProvider;
import '../../data/repositories/personal_offline_repository.dart';

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
      appBar: AppBar(
        title: const Text('My Library'),
      ),
      body: Column(
        children: [
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
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.bookmark_border_rounded, size: 64, color: Colors.grey),
                    SizedBox(height: 12),
                    Text('No titles in your watchlist or favorites yet.', style: TextStyle(color: Colors.grey)),
                  ],
                ),
              );
            }
            return ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: favs.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                final item = favs[index];
                return Card(
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
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.history, size: 64, color: Colors.grey),
                    SizedBox(height: 12),
                    Text('No watch events recorded yet.', style: TextStyle(color: Colors.grey)),
                  ],
                ),
              );
            }
            return ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: history.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                final event = history[index];
                return Card(
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
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.star_border, size: 64, color: Colors.grey),
                    SizedBox(height: 12),
                    Text('No ratings submitted yet.', style: TextStyle(color: Colors.grey)),
                  ],
                ),
              );
            }
            return ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: ratings.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                final r = ratings[index];
                return Card(
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
      default:
        // Analytics & Profile Tab
        return Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Card(
                child: Padding(
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
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: _buildMetricCard(
                      title: 'Watch Streak',
                      value: '7 Days',
                      icon: Icons.local_fire_department,
                      color: Colors.orangeAccent,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildMetricCard(
                      title: 'Total Hours',
                      value: '42.5 hrs',
                      icon: Icons.access_time_filled,
                      color: Colors.lightBlueAccent,
                    ),
                  ),
                ],
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

  Widget _buildMetricCard({
    required String title,
    required String value,
    required IconData icon,
    required Color color,
  }) {
    return Card(
      child: Padding(
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
      ),
    );
  }
}
