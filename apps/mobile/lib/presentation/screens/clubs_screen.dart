// CineVault OS — Watch Clubs & Challenges Screen
// Segmented Clubs / Challenges browser: my clubs list with a create-club
// dialog, and active challenges with per-user progress / join action.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../domain/entities/social.dart';
import '../providers/social_provider.dart';
import '../widgets/glass/glass.dart';
import 'club_detail_screen.dart';

class ClubsScreen extends ConsumerStatefulWidget {
  const ClubsScreen({super.key});

  @override
  ConsumerState<ClubsScreen> createState() => _ClubsScreenState();
}

class _ClubsScreenState extends ConsumerState<ClubsScreen> {
  int _selectedTab = 0;
  final Set<String> _joiningChallengeIds = {};

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: const GlassAppBar(title: Text('Watch Clubs')),
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
                _buildTabButton(0, 'Clubs', Icons.groups_outlined),
                _buildTabButton(1, 'Challenges', Icons.emoji_events_outlined),
              ],
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: _selectedTab == 0 ? _buildClubsTab() : _buildChallengesTab(),
          ),
        ],
      ),
      floatingActionButton: _selectedTab == 0
          ? FloatingActionButton(
              onPressed: _showCreateClubDialog,
              tooltip: 'New watch club',
              child: const Icon(Icons.add),
            )
          : null,
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

  // ---- Clubs tab ----------------------------------------------------

  Widget _buildClubsTab() {
    final clubsAsync = ref.watch(myClubsProvider);
    return clubsAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, _) => GlassErrorState(message: 'Failed to load your clubs: $error'),
      data: (clubs) {
        if (clubs.isEmpty) {
          return const GlassEmptyState(
            icon: Icons.groups_outlined,
            message: 'You have not joined or created any watch clubs yet.',
          );
        }
        return ListView.separated(
          padding: const EdgeInsets.all(16),
          itemCount: clubs.length,
          separatorBuilder: (_, __) => const SizedBox(height: 8),
          itemBuilder: (context, index) => _buildClubRow(clubs[index]),
        );
      },
    );
  }

  Widget _buildClubRow(WatchClubEntity club) {
    final hasAvatar = club.avatarUrl != null && club.avatarUrl!.isNotEmpty;
    final hasDescription = club.description != null && club.description!.isNotEmpty;

    return GlassCard(
      padding: EdgeInsets.zero,
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => ClubDetailScreen(slug: club.slug)),
        );
      },
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: AppTheme.primaryViolet.withValues(alpha: 0.2),
          backgroundImage: hasAvatar ? NetworkImage(club.avatarUrl!) : null,
          child: hasAvatar ? null : const Icon(Icons.groups, color: AppTheme.primaryViolet),
        ),
        title: Text(club.name, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: hasDescription
            ? Text(club.description!, maxLines: 2, overflow: TextOverflow.ellipsis)
            : null,
        trailing: GlassBadge(
          label: '${club.memberCount}',
          tint: AppTheme.primaryLightViolet,
          icon: Icons.person,
        ),
      ),
    );
  }

  Future<void> _showCreateClubDialog() async {
    final nameController = TextEditingController();
    final descriptionController = TextEditingController();
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
              const Text('New Watch Club', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
              const SizedBox(height: 16),
              TextFormField(
                controller: nameController,
                autofocus: true,
                decoration: const InputDecoration(labelText: 'Club name'),
                validator: (value) =>
                    (value == null || value.trim().isEmpty) ? 'Name is required' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: descriptionController,
                decoration: const InputDecoration(labelText: 'Description (optional)'),
                maxLines: 2,
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
                    onPressed: () => _submitCreateClub(
                      dialogContext,
                      formKey,
                      nameController,
                      descriptionController,
                    ),
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

  Future<void> _submitCreateClub(
    BuildContext dialogContext,
    GlobalKey<FormState> formKey,
    TextEditingController nameController,
    TextEditingController descriptionController,
  ) async {
    if (!(formKey.currentState?.validate() ?? false)) return;
    try {
      final description = descriptionController.text.trim();
      await ref.read(socialRepositoryProvider).createWatchClub(
            name: nameController.text.trim(),
            description: description.isEmpty ? null : description,
          );
      ref.invalidate(myClubsProvider);
      if (dialogContext.mounted) Navigator.pop(dialogContext);
    } catch (e) {
      if (!dialogContext.mounted) return;
      ScaffoldMessenger.of(dialogContext).showSnackBar(
        SnackBar(content: Text('Failed to create club: $e')),
      );
    }
  }

  // ---- Challenges tab -------------------------------------------------

  Widget _buildChallengesTab() {
    final challengesAsync = ref.watch(activeChallengesProvider);
    return challengesAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, _) => GlassErrorState(message: 'Failed to load active challenges: $error'),
      data: (challenges) {
        if (challenges.isEmpty) {
          return const GlassEmptyState(
            icon: Icons.emoji_events_outlined,
            message: 'No active challenges right now. Check back soon.',
          );
        }
        return ListView.separated(
          padding: const EdgeInsets.all(16),
          itemCount: challenges.length,
          separatorBuilder: (_, __) => const SizedBox(height: 8),
          itemBuilder: (context, index) => _buildChallengeRow(challenges[index]),
        );
      },
    );
  }

  Widget _buildChallengeRow(ChallengeEntity challenge) {
    final hasJoined = challenge.myProgress != null;
    final hasDescription = challenge.description != null && challenge.description!.isNotEmpty;
    final double progressRatio = hasJoined && challenge.goalCount > 0
        ? (challenge.myProgress! / challenge.goalCount).clamp(0.0, 1.0).toDouble()
        : 0.0;
    final isJoining = _joiningChallengeIds.contains(challenge.challengeId);

    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  challenge.title,
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                ),
              ),
              if (challenge.myCompleted)
                const Padding(
                  padding: EdgeInsets.only(left: 4),
                  child: Icon(Icons.check_circle, color: AppTheme.stateSuccess, size: 20),
                ),
              const SizedBox(width: 8),
              GlassBadge(
                label: '${challenge.participantCount}',
                tint: AppTheme.secondaryCyan,
                icon: Icons.groups,
              ),
            ],
          ),
          if (hasDescription) ...[
            const SizedBox(height: 4),
            Text(
              challenge.description!,
              style: const TextStyle(color: AppTheme.textMuted, fontSize: 13),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],
          const SizedBox(height: 12),
          if (hasJoined)
            _buildChallengeProgress(challenge, progressRatio)
          else
            Align(
              alignment: Alignment.centerRight,
              child: ElevatedButton(
                onPressed: isJoining ? null : () => _joinChallenge(challenge.challengeId),
                child: isJoining
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Text('Join'),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildChallengeProgress(ChallengeEntity challenge, double progressRatio) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: progressRatio,
            minHeight: 6,
            backgroundColor: AppTheme.cardElevated,
            valueColor: AlwaysStoppedAnimation<Color>(
              challenge.myCompleted ? AppTheme.stateSuccess : AppTheme.primaryViolet,
            ),
          ),
        ),
        const SizedBox(height: 6),
        Text(
          '${challenge.myProgress} / ${challenge.goalCount}',
          style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
        ),
      ],
    );
  }

  Future<void> _joinChallenge(String challengeId) async {
    setState(() => _joiningChallengeIds.add(challengeId));
    try {
      await ref.read(socialRepositoryProvider).joinChallenge(challengeId);
      ref.invalidate(activeChallengesProvider);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to join challenge: $e')),
      );
    } finally {
      if (mounted) setState(() => _joiningChallengeIds.remove(challengeId));
    }
  }
}
