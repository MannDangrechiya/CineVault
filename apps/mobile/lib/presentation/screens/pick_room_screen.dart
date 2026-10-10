// CineVault OS — Pick Room Screen (Part 3.1)
// View/vote screen for a group "pick room": shows candidates with live
// upvote percentages, lets any viewer cast an upvote while OPEN, and
// surfaces the winning title once the room is RESOLVED.
// See apps/mobile/lib/domain/entities/social.dart (PickRoomEntity,
// CandidateSummaryEntity) and social_provider.dart (socialRepositoryProvider).

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/config/api_config.dart';
import '../../core/theme/app_theme.dart';
import '../../domain/entities/social.dart';
import '../providers/auth_provider.dart';
import '../providers/social_provider.dart';
import '../widgets/glass/glass.dart';

class PickRoomScreen extends ConsumerStatefulWidget {
  const PickRoomScreen({super.key, required this.slug});

  final String slug;

  @override
  ConsumerState<PickRoomScreen> createState() => _PickRoomScreenState();
}

class _PickRoomScreenState extends ConsumerState<PickRoomScreen> {
  late Future<PickRoomEntity> _roomFuture;

  // Title IDs with a vote in flight, so each candidate row can show its own
  // spinner without blocking the rest of the list.
  final Set<String> _votingTitleIds = {};
  bool _isClosingVoting = false;

  @override
  void initState() {
    super.initState();
    _roomFuture = _fetchRoom();
  }

  Future<PickRoomEntity> _fetchRoom() {
    return ref.read(socialRepositoryProvider).getPickRoom(widget.slug);
  }

  Future<void> _refreshRoom() async {
    final refreshed = _fetchRoom();
    setState(() {
      _roomFuture = refreshed;
    });
    await refreshed;
  }

  Future<void> _castUpvote(String titleId) async {
    if (_votingTitleIds.contains(titleId)) return;

    setState(() {
      _votingTitleIds.add(titleId);
    });

    try {
      await ref
          .read(socialRepositoryProvider)
          .castPickVote(slug: widget.slug, titleId: titleId);
      await _refreshRoom();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not cast vote: $e')),
      );
    } finally {
      if (mounted) {
        setState(() {
          _votingTitleIds.remove(titleId);
        });
      }
    }
  }

  Future<void> _closeVoting() async {
    setState(() {
      _isClosingVoting = true;
    });

    try {
      await ref.read(socialRepositoryProvider).closePickRoom(widget.slug);
      await _refreshRoom();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not close voting: $e')),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isClosingVoting = false;
        });
      }
    }
  }

  Future<void> _shareRoomLink() async {
    final link = '${ApiConfig.webAppUrl}/pick/${widget.slug}';
    await Clipboard.setData(ClipboardData(text: link));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Room link copied to clipboard')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: GlassAppBar(
        title: const Text('Pick Room'),
        actions: [
          IconButton(
            icon: const Icon(Icons.share),
            tooltip: 'Share Room Link',
            onPressed: _shareRoomLink,
          ),
        ],
      ),
      body: Column(
        children: [
          GlassAppBar.contentSpacer(context),
          Expanded(
            child: FutureBuilder<PickRoomEntity>(
              future: _roomFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(
                    child: CircularProgressIndicator(
                      semanticsLabel: 'Loading pick room',
                    ),
                  );
                }

                if (snapshot.hasError) {
                  return GlassErrorState(
                    message: '${snapshot.error}',
                    onRetry: _refreshRoom,
                  );
                }

                final room = snapshot.data;
                if (room == null) {
                  return GlassErrorState(
                    message: 'Pick room not found.',
                    onRetry: _refreshRoom,
                  );
                }

                return RefreshIndicator(
                  onRefresh: _refreshRoom,
                  child: _PickRoomBody(
                    room: room,
                    votingTitleIds: _votingTitleIds,
                    isClosingVoting: _isClosingVoting,
                    onUpvote: _castUpvote,
                    onCloseVoting: _closeVoting,
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

class _PickRoomBody extends ConsumerWidget {
  const _PickRoomBody({
    required this.room,
    required this.votingTitleIds,
    required this.isClosingVoting,
    required this.onUpvote,
    required this.onCloseVoting,
  });

  final PickRoomEntity room;
  final Set<String> votingTitleIds;
  final bool isClosingVoting;
  final Future<void> Function(String titleId) onUpvote;
  final Future<void> Function() onCloseVoting;

  bool get _isOpen => room.status == 'OPEN';

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final textTheme = Theme.of(context).textTheme;
    final currentUserId = ref.watch(authProvider).session?.userId;
    final isHost = currentUserId != null && currentUserId == room.hostId;

    return ListView(
      padding: const EdgeInsets.all(16),
      // Always allow pull-to-refresh even when content is shorter than
      // the viewport.
      physics: const AlwaysScrollableScrollPhysics(),
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Text(room.title, style: textTheme.headlineMedium),
            ),
            const SizedBox(width: 8),
            _StatusBadge(status: room.status),
          ],
        ),
        const SizedBox(height: 6),
        Text(
          'Hosted by ${room.hostName ?? 'Unknown host'}',
          style: textTheme.bodyMedium,
        ),
        const SizedBox(height: 16),
        if (room.status == 'RESOLVED' && room.winningTitleName != null)
          GlassCard(
            margin: const EdgeInsets.only(bottom: 16),
            tintColor: AppTheme.accentGold,
            child: Row(
              children: [
                const Text('🏆', style: TextStyle(fontSize: 28)),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'Winner: ${room.winningTitleName}',
                    style: textTheme.titleLarge,
                  ),
                ),
              ],
            ),
          ),
        if (_isOpen && isHost)
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              icon: isClosingVoting
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.lock_outline),
              label: Text(isClosingVoting ? 'Closing Voting...' : 'Close Voting'),
              onPressed: isClosingVoting ? null : onCloseVoting,
            ),
          ),
        const SizedBox(height: 16),
        Text('Candidates', style: textTheme.titleLarge),
        const SizedBox(height: 8),
        if (room.candidates.isEmpty)
          const GlassEmptyState(
            icon: Icons.how_to_vote_outlined,
            message: 'No candidates in this pick room.',
            margin: EdgeInsets.zero,
          )
        else
          ...room.candidates.map(
            (candidate) => _CandidateRow(
              candidate: candidate,
              totalVotes: room.totalVotes,
              isOpen: _isOpen,
              isVoting: votingTitleIds.contains(candidate.titleId),
              onUpvote: () => onUpvote(candidate.titleId),
            ),
          ),
      ],
    );
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final isOpen = status == 'OPEN';
    return GlassBadge(
      label: status,
      tint: isOpen ? AppTheme.stateSuccess : AppTheme.textMuted,
      icon: isOpen ? Icons.how_to_vote : Icons.lock_outline,
    );
  }
}

class _CandidateRow extends StatelessWidget {
  const _CandidateRow({
    required this.candidate,
    required this.totalVotes,
    required this.isOpen,
    required this.isVoting,
    required this.onUpvote,
  });

  final CandidateSummaryEntity candidate;
  final int totalVotes;
  final bool isOpen;
  final bool isVoting;
  final VoidCallback onUpvote;

  double get _voteFraction => totalVotes == 0 ? 0.0 : candidate.upvotes / totalVotes;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return GlassCard(
      margin: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 48,
            height: 68,
            decoration: BoxDecoration(
              color: AppTheme.cardElevated,
              borderRadius: BorderRadius.circular(4),
            ),
            clipBehavior: Clip.antiAlias,
            child: candidate.posterUrl != null && candidate.posterUrl!.isNotEmpty
                ? Image.network(
                    candidate.posterUrl!,
                    fit: BoxFit.cover,
                    errorBuilder: (context, error, stackTrace) => const Icon(
                      Icons.movie,
                      color: AppTheme.primaryLightViolet,
                      size: 24,
                    ),
                  )
                : const Icon(
                    Icons.movie,
                    color: AppTheme.primaryLightViolet,
                    size: 24,
                  ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  candidate.canonicalTitle,
                  style: textTheme.titleMedium,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                if (candidate.productionYear != null)
                  Text('${candidate.productionYear}', style: textTheme.bodySmall),
                const SizedBox(height: 8),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: _voteFraction,
                    minHeight: 6,
                    backgroundColor: AppTheme.cardElevated,
                    valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.primaryViolet),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '${candidate.upvotes} vote${candidate.upvotes == 1 ? '' : 's'} '
                  '(${(_voteFraction * 100).round()}%)',
                  style: textTheme.bodySmall,
                ),
              ],
            ),
          ),
          if (isOpen) ...[
            const SizedBox(width: 8),
            IconButton(
              icon: isVoting
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.thumb_up_outlined),
              tooltip: 'Upvote',
              color: AppTheme.primaryLightViolet,
              onPressed: isVoting ? null : onUpvote,
            ),
          ],
        ],
      ),
    );
  }
}
