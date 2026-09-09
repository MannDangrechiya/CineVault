// CineVault OS — Watch Club Detail Screen
// Club profile, member roster, join action, and recent activity feed.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../domain/entities/social.dart';
import '../providers/social_provider.dart';
import '../widgets/glass/glass.dart';

class ClubDetailScreen extends ConsumerStatefulWidget {
  const ClubDetailScreen({super.key, required this.slug});

  final String slug;

  @override
  ConsumerState<ClubDetailScreen> createState() => _ClubDetailScreenState();
}

class _ClubDetailScreenState extends ConsumerState<ClubDetailScreen> {
  late Future<ClubDetailEntity> _clubDetailFuture;
  late Future<List<ClubActivityEntity>> _feedFuture;
  bool _isJoining = false;

  @override
  void initState() {
    super.initState();
    _loadClub();
  }

  void _loadClub() {
    final repository = ref.read(socialRepositoryProvider);
    _clubDetailFuture = repository.getWatchClub(widget.slug);
    _feedFuture = repository.getClubFeed(widget.slug);
  }

  Future<void> _joinClub() async {
    setState(() => _isJoining = true);
    try {
      await ref.read(socialRepositoryProvider).joinWatchClub(widget.slug);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Joined the club!')),
      );
      setState(_loadClub);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to join club: $e')),
      );
    } finally {
      if (mounted) setState(() => _isJoining = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: const GlassAppBar(title: Text('Watch Club')),
      body: Column(
        children: [
          GlassAppBar.contentSpacer(context),
          Expanded(
            child: FutureBuilder<ClubDetailEntity>(
              future: _clubDetailFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.hasError) {
                  return _buildErrorBanner('Failed to load club: ${snapshot.error}');
                }
                final detail = snapshot.data;
                if (detail == null) {
                  return _buildErrorBanner('Club not found.');
                }
                return _buildContent(detail);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildContent(ClubDetailEntity detail) {
    final club = detail.club;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildClubHeader(club),
        const SizedBox(height: 16),
        SizedBox(
          width: double.infinity,
          child: ElevatedButton.icon(
            // NOTE: this always shows "Join Club" rather than detecting
            // existing membership — this screen does not have the current
            // authenticated user's id wired in, so it cannot reliably
            // compare it against `detail.members`. Wire in the current
            // user id (see auth_provider.dart) to add proper
            // "already a member" detection here.
            onPressed: _isJoining ? null : _joinClub,
            icon: _isJoining
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.group_add_outlined),
            label: const Text('Join Club'),
          ),
        ),
        const SizedBox(height: 24),
        Text(
          'Members (${detail.members.length})',
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
        ),
        const SizedBox(height: 8),
        ...detail.members.map(_buildMemberRow),
        const SizedBox(height: 24),
        const Text('Activity Feed', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        const SizedBox(height: 8),
        _buildActivityFeed(),
      ],
    );
  }

  Widget _buildClubHeader(WatchClubEntity club) {
    final hasAvatar = club.avatarUrl != null && club.avatarUrl!.isNotEmpty;
    final hasDescription = club.description != null && club.description!.isNotEmpty;

    return GlassCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CircleAvatar(
            radius: 28,
            backgroundColor: AppTheme.primaryViolet.withValues(alpha: 0.2),
            backgroundImage: hasAvatar ? NetworkImage(club.avatarUrl!) : null,
            child: hasAvatar
                ? null
                : const Icon(Icons.groups, color: AppTheme.primaryViolet, size: 28),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(club.name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                if (hasDescription) ...[
                  const SizedBox(height: 4),
                  Text(club.description!, style: const TextStyle(color: AppTheme.textSecondary)),
                ],
                const SizedBox(height: 6),
                GlassBadge(
                  label: '${club.memberCount} members',
                  tint: AppTheme.primaryLightViolet,
                  icon: Icons.person,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMemberRow(ClubMembershipEntity member) {
    return GlassCard(
      margin: const EdgeInsets.only(bottom: 8),
      padding: EdgeInsets.zero,
      child: ListTile(
        leading: const Icon(Icons.person_outline, color: AppTheme.primaryLightViolet),
        title: Text(member.userName ?? 'Unknown member'),
        trailing: GlassBadge(label: member.role, tint: AppTheme.secondaryCyan),
      ),
    );
  }

  Widget _buildActivityFeed() {
    return FutureBuilder<List<ClubActivityEntity>>(
      future: _feedFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Padding(
            padding: EdgeInsets.symmetric(vertical: 16),
            child: Center(child: CircularProgressIndicator()),
          );
        }
        if (snapshot.hasError) {
          return _buildErrorBanner('Failed to load activity feed: ${snapshot.error}');
        }
        final activities = snapshot.data ?? const <ClubActivityEntity>[];
        if (activities.isEmpty) {
          return const Padding(
            padding: EdgeInsets.symmetric(vertical: 8),
            child: Text(
              'No recent activity in this club yet.',
              style: TextStyle(color: AppTheme.textMuted),
            ),
          );
        }
        return Column(children: activities.map(_buildActivityRow).toList());
      },
    );
  }

  Widget _buildActivityRow(ClubActivityEntity activity) {
    return GlassCard(
      margin: const EdgeInsets.only(bottom: 8),
      padding: EdgeInsets.zero,
      child: ListTile(
        leading: const Icon(Icons.bolt_outlined, color: AppTheme.accentGold),
        title: Text(activity.userName ?? 'A member', style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text(activity.activityType),
        trailing: Text(
          activity.createdAt.split('T').first,
          style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
        ),
      ),
    );
  }

  Widget _buildErrorBanner(String message) {
    return Center(
      child: GlassCard(
        margin: const EdgeInsets.all(24),
        tintColor: AppTheme.stateError,
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, color: AppTheme.stateError),
            const SizedBox(width: 8),
            Flexible(
              child: Text(message, style: const TextStyle(color: AppTheme.stateError)),
            ),
          ],
        ),
      ),
    );
  }
}
