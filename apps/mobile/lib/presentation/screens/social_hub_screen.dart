// CineVault OS — Social Hub Screen (PLAN.md Part 3.2)
// Friends & pending requests, taste-match leaderboard, and peer recommendations inbox.
// Built entirely on the already-complete Part 3.1 social data layer
// (domain/entities/social.dart, presentation/providers/social_provider.dart).

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../domain/entities/social.dart';
import '../providers/social_provider.dart';
import '../widgets/glass/glass.dart';

class SocialHubScreen extends ConsumerStatefulWidget {
  const SocialHubScreen({super.key});

  @override
  ConsumerState<SocialHubScreen> createState() => _SocialHubScreenState();
}

class _SocialHubScreenState extends ConsumerState<SocialHubScreen> {
  int _selectedTab = 0;
  String _leaderboardPeriod = 'weekly';
  String _recommendationsRole = 'received';
  final Set<String> _compareLoadingIds = {};

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: const GlassAppBar(title: Text('Social Hub')),
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
                _buildTabButton(0, 'Friends', Icons.people_outline),
                _buildTabButton(1, 'Leaderboard', Icons.leaderboard_outlined),
                _buildTabButton(2, 'Recommendations', Icons.recommend_outlined),
              ],
            ),
          ),
          const Divider(height: 1),

          Expanded(child: _buildTabBody(_selectedTab)),
        ],
      ),
    );
  }

  Widget _buildTabButton(int index, String label, IconData icon) {
    final isSelected = _selectedTab == index;
    return InkWell(
      onTap: () => setState(() => _selectedTab = index),
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

  Widget _buildTabBody(int tabIndex) {
    switch (tabIndex) {
      case 0:
        return _buildFriendsTab();
      case 1:
        return _buildLeaderboardTab();
      case 2:
      default:
        return _buildRecommendationsTab();
    }
  }

  // ── Friends Tab ──────────────────────────────────────────────────────────

  Widget _buildFriendsTab() {
    final friendshipsAsync = ref.watch(friendshipsProvider);

    return friendshipsAsync.when(
      data: (friendships) {
        final accepted = ref.watch(acceptedFriendsProvider);
        final pending = friendships.where((f) => f.status == 'PENDING').toList();

        if (accepted.isEmpty && pending.isEmpty) {
          return _buildEmptyState(
            icon: Icons.people_outline,
            message: 'No friends yet. Send a friend request to get started.',
          );
        }

        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (pending.isNotEmpty) ...[
              const _SectionHeader('Pending Requests'),
              const SizedBox(height: 8),
              ...pending.map((f) => Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: _buildPendingRow(f),
                  )),
              const SizedBox(height: 16),
            ],
            if (accepted.isNotEmpty) ...[
              const _SectionHeader('Friends'),
              const SizedBox(height: 8),
              ...accepted.map((f) => Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: _buildFriendRow(f),
                  )),
            ],
          ],
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, stack) => _buildErrorState(error.toString()),
    );
  }

  Widget _buildFriendRow(FriendshipEntity friend) {
    final isLoading = _compareLoadingIds.contains(friend.friendId);

    return GlassCard(
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  friend.friendName ?? friend.friendUsername ?? 'Unknown',
                  style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                ),
                if (friend.friendUsername != null)
                  Text(
                    '@${friend.friendUsername}',
                    style: const TextStyle(fontSize: 12, color: AppTheme.textMuted),
                  ),
                if (friend.status != 'ACCEPTED') ...[
                  const SizedBox(height: 6),
                  GlassBadge(label: friend.status, tint: _statusColor(friend.status)),
                ],
              ],
            ),
          ),
          TextButton(
            onPressed: isLoading ? null : () => _compareTaste(friend),
            child: isLoading
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Text('Compare Taste →'),
          ),
        ],
      ),
    );
  }

  Widget _buildPendingRow(FriendshipEntity friend) {
    return GlassCard(
      tintColor: AppTheme.stateWarning,
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  friend.friendName ?? friend.friendUsername ?? 'Unknown',
                  style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                ),
                const SizedBox(height: 4),
                const GlassBadge(label: 'PENDING', tint: AppTheme.stateWarning),
              ],
            ),
          ),
          TextButton(
            onPressed: () => _respondToRequest(friend, 'ACCEPTED'),
            child: const Text('Accept'),
          ),
          TextButton(
            onPressed: () => _respondToRequest(friend, 'BLOCKED'),
            style: TextButton.styleFrom(foregroundColor: AppTheme.stateError),
            child: const Text('Decline'),
          ),
        ],
      ),
    );
  }

  Future<void> _compareTaste(FriendshipEntity friend) async {
    setState(() => _compareLoadingIds.add(friend.friendId));
    try {
      final compatibility = await ref.read(socialRepositoryProvider).getFriendCompatibility(friend.friendId);
      if (!mounted) return;
      await GlassModalSheet.showDialogPanel<void>(
        context: context,
        builder: (dialogContext) => _buildCompatibilityDialog(dialogContext, compatibility),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to load compatibility: $e')),
      );
    } finally {
      if (mounted) setState(() => _compareLoadingIds.remove(friend.friendId));
    }
  }

  Widget _buildCompatibilityDialog(BuildContext dialogContext, CompatibilityEntity compatibility) {
    final tierColor = _tierColor(compatibility.tasteTier);
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            compatibility.friendName ?? compatibility.friendUsername ?? 'Taste Compatibility',
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Text(
                '${compatibility.compatibilityScore.toStringAsFixed(0)}%',
                style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
              ),
              const SizedBox(width: 12),
              GlassBadge(label: compatibility.tasteTier, tint: tierColor),
            ],
          ),
          const SizedBox(height: 16),
          if (compatibility.sharedGenres.isNotEmpty) ...[
            const Text('Shared Genres', style: TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
            const SizedBox(height: 6),
            _buildChipWrap(compatibility.sharedGenres, AppTheme.primaryViolet),
            const SizedBox(height: 12),
          ],
          if (compatibility.sharedDirectors.isNotEmpty) ...[
            const Text('Shared Directors', style: TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
            const SizedBox(height: 6),
            _buildChipWrap(compatibility.sharedDirectors, AppTheme.secondaryCyan),
            const SizedBox(height: 12),
          ],
          if (compatibility.sharedFavoriteTitles.isNotEmpty) ...[
            const Text('Shared Favorite Titles', style: TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
            const SizedBox(height: 6),
            _buildChipWrap(compatibility.sharedFavoriteTitles, AppTheme.accentGold),
            const SizedBox(height: 12),
          ],
          Align(
            alignment: Alignment.centerRight,
            child: TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(),
              child: const Text('Close'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildChipWrap(List<String> items, Color tint) {
    return Wrap(
      spacing: 6,
      runSpacing: 6,
      children: items.map((item) => GlassBadge(label: item, tint: tint)).toList(),
    );
  }

  Future<void> _respondToRequest(FriendshipEntity friend, String status) async {
    try {
      await ref.read(socialRepositoryProvider).updateFriendshipStatus(
            friendshipId: friend.friendshipId,
            status: status,
          );
      ref.invalidate(friendshipsProvider);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to update request: $e')),
      );
    }
  }

  Color _tierColor(String tier) {
    switch (tier) {
      case 'Oracle':
        return AppTheme.accentGold;
      case 'Critic':
        return AppTheme.secondaryCyan;
      case 'Regular':
        return AppTheme.primaryViolet;
      case 'Curious':
      default:
        return AppTheme.textMuted;
    }
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'ACCEPTED':
        return AppTheme.stateSuccess;
      case 'BLOCKED':
        return AppTheme.stateError;
      case 'PENDING':
      default:
        return AppTheme.stateWarning;
    }
  }

  // ── Leaderboard Tab ──────────────────────────────────────────────────────

  Widget _buildLeaderboardTab() {
    final leaderboardAsync = ref.watch(socialLeaderboardProvider(_leaderboardPeriod));

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Row(
            children: [
              _buildPeriodChip('weekly', 'Weekly'),
              const SizedBox(width: 8),
              _buildPeriodChip('monthly', 'Monthly'),
              const SizedBox(width: 8),
              _buildPeriodChip('all_time', 'All Time'),
            ],
          ),
        ),
        Expanded(
          child: leaderboardAsync.when(
            data: (leaderboard) {
              if (leaderboard.entries.isEmpty) {
                return _buildEmptyState(
                  icon: Icons.leaderboard_outlined,
                  message: 'No leaderboard data for this period yet.',
                );
              }
              return ListView.separated(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: leaderboard.entries.length,
                separatorBuilder: (_, __) => const SizedBox(height: 8),
                itemBuilder: (context, index) {
                  final entry = leaderboard.entries[index];
                  return GlassCard(
                    tintColor: entry.isCurrentUser ? AppTheme.primaryViolet : null,
                    child: Row(
                      children: [
                        GlassBadge(label: '#${entry.rank}', tint: AppTheme.accentGold),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                entry.name ?? entry.username ?? 'Unknown',
                                style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                              ),
                              Text(
                                '${entry.watchCount} watched • ${entry.watchHours.toStringAsFixed(1)} hrs',
                                style: const TextStyle(fontSize: 12, color: AppTheme.textMuted),
                              ),
                            ],
                          ),
                        ),
                        if (entry.isCurrentUser) const GlassBadge(label: 'You', tint: AppTheme.secondaryCyan),
                      ],
                    ),
                  );
                },
              );
            },
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, stack) => _buildErrorState(error.toString()),
          ),
        ),
      ],
    );
  }

  Widget _buildPeriodChip(String period, String label) {
    final isSelected = _leaderboardPeriod == period;
    return ChoiceChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (_) => setState(() => _leaderboardPeriod = period),
      selectedColor: AppTheme.primaryViolet,
      labelStyle: TextStyle(color: isSelected ? Colors.white : AppTheme.textSecondary),
    );
  }

  // ── Recommendations Tab ──────────────────────────────────────────────────

  Widget _buildRecommendationsTab() {
    final recommendationsAsync = ref.watch(recommendationsInboxProvider(_recommendationsRole));

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Row(
            children: [
              _buildRoleChip('received', 'Received'),
              const SizedBox(width: 8),
              _buildRoleChip('sent', 'Sent'),
            ],
          ),
        ),
        Expanded(
          child: recommendationsAsync.when(
            data: (recommendations) {
              if (recommendations.isEmpty) {
                return _buildEmptyState(
                  icon: Icons.recommend_outlined,
                  message: 'No recommendations here yet.',
                );
              }
              return ListView.separated(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: recommendations.length,
                separatorBuilder: (_, __) => const SizedBox(height: 8),
                itemBuilder: (context, index) => _buildRecommendationRow(recommendations[index]),
              );
            },
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, stack) => _buildErrorState(error.toString()),
          ),
        ),
      ],
    );
  }

  Widget _buildRoleChip(String role, String label) {
    final isSelected = _recommendationsRole == role;
    return ChoiceChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (_) => setState(() => _recommendationsRole = role),
      selectedColor: AppTheme.primaryViolet,
      labelStyle: TextStyle(color: isSelected ? Colors.white : AppTheme.textSecondary),
    );
  }

  Widget _buildRecommendationRow(RecommendationEntity recommendation) {
    final showActions = _recommendationsRole == 'received' && recommendation.status == 'SENT';

    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (recommendation.posterUrl != null)
                ClipRRect(
                  borderRadius: BorderRadius.circular(6),
                  child: Image.network(
                    recommendation.posterUrl!,
                    width: 44,
                    height: 64,
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => const SizedBox(width: 44, height: 64),
                  ),
                )
              else
                const Icon(Icons.movie_outlined, color: AppTheme.textMuted, size: 44),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      recommendation.canonicalTitle ?? recommendation.titleId,
                      style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      _recommendationsRole == 'received'
                          ? 'From ${recommendation.senderName ?? "someone"}'
                          : 'To ${recommendation.recipientName ?? "someone"}',
                      style: const TextStyle(fontSize: 12, color: AppTheme.textMuted),
                    ),
                    if (recommendation.contextNote != null && recommendation.contextNote!.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(
                        recommendation.contextNote!,
                        style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, fontStyle: FontStyle.italic),
                      ),
                    ],
                    const SizedBox(height: 6),
                    GlassBadge(label: recommendation.status, tint: _recommendationStatusColor(recommendation.status)),
                  ],
                ),
              ),
            ],
          ),
          if (showActions) ...[
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton(
                  onPressed: () => _respondToRecommendation(recommendation, 'ACCEPTED'),
                  child: const Text('Accept'),
                ),
                TextButton(
                  onPressed: () => _respondToRecommendation(recommendation, 'REJECTED'),
                  style: TextButton.styleFrom(foregroundColor: AppTheme.stateError),
                  child: const Text('Reject'),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Future<void> _respondToRecommendation(RecommendationEntity recommendation, String status) async {
    try {
      await ref.read(socialRepositoryProvider).updateRecommendationStatus(
            id: recommendation.recommendationId,
            status: status,
          );
      ref.invalidate(recommendationsInboxProvider(_recommendationsRole));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to update recommendation: $e')),
      );
    }
  }

  Color _recommendationStatusColor(String status) {
    switch (status) {
      case 'ACCEPTED':
      case 'WATCHED':
      case 'RATED':
        return AppTheme.stateSuccess;
      case 'REJECTED':
        return AppTheme.stateError;
      case 'SENT':
      default:
        return AppTheme.stateWarning;
    }
  }

  // ── Shared empty / error states ─────────────────────────────────────────

  Widget _buildEmptyState({required IconData icon, required String message}) {
    return Center(
      child: GlassCard(
        margin: const EdgeInsets.all(24),
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 64, color: Colors.grey),
            const SizedBox(height: 12),
            Text(message, style: const TextStyle(color: Colors.grey), textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorState(String message) {
    return Center(
      child: GlassCard(
        margin: const EdgeInsets.all(16),
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
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader(this.label);

  final String label;

  @override
  Widget build(BuildContext context) {
    return Text(
      label,
      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.textSecondary),
    );
  }
}
