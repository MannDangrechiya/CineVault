// CineVault OS — Invite a Friend Screen (Part 3.6)
// Create + share an invite link, view referral stats, and a manual-entry
// fallback for accepting an invite token (no deep-link routing infra yet —
// see PLAN.md 3.6 for the /invite/{token} taste-preview + accept flow this
// section stands in for).

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../domain/entities/social.dart';
import '../providers/social_provider.dart';
import '../widgets/glass/glass.dart';

class InviteScreen extends ConsumerStatefulWidget {
  const InviteScreen({super.key});

  @override
  ConsumerState<InviteScreen> createState() => _InviteScreenState();
}

class _InviteScreenState extends ConsumerState<InviteScreen> {
  final TextEditingController _tokenController = TextEditingController();

  InviteTokenEntity? _inviteToken;
  bool _isCreatingInvite = false;
  String? _createInviteError;

  InvitePreviewEntity? _invitePreview;
  bool _isPreviewing = false;
  String? _previewError;

  bool _isAccepting = false;
  String? _acceptError;

  @override
  void dispose() {
    _tokenController.dispose();
    super.dispose();
  }

  Future<void> _createInvite() async {
    setState(() {
      _isCreatingInvite = true;
      _createInviteError = null;
    });

    try {
      final token = await ref.read(socialRepositoryProvider).createInviteToken();
      setState(() {
        _inviteToken = token;
        _isCreatingInvite = false;
      });
    } catch (e) {
      setState(() {
        _isCreatingInvite = false;
        _createInviteError = e.toString();
      });
    }
  }

  Future<void> _copyInviteLink() async {
    final url = _inviteToken?.inviteUrl;
    if (url == null || url.isEmpty) return;

    await Clipboard.setData(ClipboardData(text: url));
    if (!mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('Invite link copied to clipboard')));
  }

  Future<void> _previewInvite() async {
    final token = _tokenController.text.trim();
    if (token.isEmpty) return;

    setState(() {
      _isPreviewing = true;
      _previewError = null;
      _invitePreview = null;
    });

    try {
      final preview = await ref.read(socialRepositoryProvider).getInvitePreview(token);
      setState(() {
        _invitePreview = preview;
        _isPreviewing = false;
      });
    } catch (e) {
      setState(() {
        _isPreviewing = false;
        _previewError = e.toString();
      });
    }
  }

  Future<void> _acceptInvite() async {
    final preview = _invitePreview;
    if (preview == null) return;

    setState(() {
      _isAccepting = true;
      _acceptError = null;
    });

    try {
      await ref.read(socialRepositoryProvider).acceptInviteToken(preview.token);
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Invite accepted — you are now connected')));
      Navigator.pop(context);
    } catch (e) {
      setState(() {
        _isAccepting = false;
        _acceptError = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: const GlassAppBar(title: Text('Invite a Friend')),
      body: ListView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        children: [
          GlassAppBar.contentSpacer(context),
          const SizedBox(height: 8),
          _buildCreateShareSection(textTheme),
          const SizedBox(height: 16),
          _buildReferralStatsSection(textTheme),
          const SizedBox(height: 16),
          _buildAcceptInviteSection(textTheme),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildCreateShareSection(TextTheme textTheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Invite a Friend', style: textTheme.titleMedium),
              const SizedBox(height: 4),
              Text(
                'Generate a personal invite link and share it with a friend.',
                style: textTheme.bodySmall?.copyWith(color: AppTheme.textMuted),
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  icon: _isCreatingInvite
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.link),
                  label: Text(
                    _isCreatingInvite ? 'Generating…' : 'Generate Invite Link',
                  ),
                  onPressed: _isCreatingInvite ? null : _createInvite,
                ),
              ),
              if (_inviteToken != null) ...[
                const SizedBox(height: 16),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  decoration: BoxDecoration(
                    color: AppTheme.cardElevated,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppTheme.borderSubtle),
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: SelectableText(
                          _inviteToken!.inviteUrl,
                          style: textTheme.bodyMedium,
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.copy),
                        tooltip: 'Copy Link',
                        onPressed: _copyInviteLink,
                      ),
                    ],
                  ),
                ),
                if (_inviteToken!.expiresAt != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    'Expires: ${_inviteToken!.expiresAt}',
                    style: textTheme.bodySmall?.copyWith(color: AppTheme.textMuted),
                  ),
                ],
              ],
            ],
          ),
        ),
        if (_createInviteError != null) ...[
          const SizedBox(height: 8),
          _buildErrorBanner(_createInviteError!),
        ],
      ],
    );
  }

  Widget _buildReferralStatsSection(TextTheme textTheme) {
    final statsAsync = ref.watch(referralStatsProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Your Referral Stats', style: textTheme.titleMedium),
        const SizedBox(height: 8),
        statsAsync.when(
          loading: () => const Center(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: CircularProgressIndicator(semanticsLabel: 'Loading referral stats'),
            ),
          ),
          error: (error, stackTrace) => _buildErrorBanner(error.toString()),
          data: (stats) => Row(
            children: [
              Expanded(
                child: _buildStatTile(
                  label: 'Invites Sent',
                  value: stats.totalInvitesSent,
                  icon: Icons.send,
                  tint: AppTheme.primaryLightViolet,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildStatTile(
                  label: 'Conversions',
                  value: stats.totalConversions,
                  icon: Icons.how_to_reg,
                  tint: AppTheme.secondaryCyan,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildStatTile(
                  label: 'Qualified',
                  value: stats.qualifiedReferrals,
                  icon: Icons.verified,
                  tint: AppTheme.accentGold,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildStatTile({
    required String label,
    required int value,
    required IconData icon,
    required Color tint,
  }) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '$value',
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.bold,
              color: AppTheme.textPrimary,
            ),
          ),
          const SizedBox(height: 6),
          GlassBadge(label: label, tint: tint, icon: icon),
        ],
      ),
    );
  }

  Widget _buildAcceptInviteSection(TextTheme textTheme) {
    final preview = _invitePreview;
    final canAccept = preview != null && !preview.isExpired && !preview.isConverted;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Have an Invite?', style: textTheme.titleMedium),
        const SizedBox(height: 4),
        Text(
          'Paste an invite token below to preview and accept it.',
          style: textTheme.bodySmall?.copyWith(color: AppTheme.textMuted),
        ),
        const SizedBox(height: 12),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextFormField(
                controller: _tokenController,
                decoration: const InputDecoration(
                  labelText: 'Invite Token',
                  hintText: 'Paste the invite token here',
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  icon: _isPreviewing
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.search),
                  label: Text(_isPreviewing ? 'Loading Preview…' : 'Preview'),
                  onPressed: _isPreviewing ? null : _previewInvite,
                ),
              ),
            ],
          ),
        ),
        if (_previewError != null) ...[
          const SizedBox(height: 8),
          _buildErrorBanner(_previewError!),
        ],
        if (preview != null) ...[
          const SizedBox(height: 12),
          GlassCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  preview.inviterName ?? 'A CineVault member',
                  style: textTheme.titleMedium,
                ),
                const SizedBox(height: 4),
                Text(
                  '${preview.totalWatchedCount} titles watched',
                  style: textTheme.bodySmall?.copyWith(color: AppTheme.textMuted),
                ),
                if (preview.isExpired || preview.isConverted) ...[
                  const SizedBox(height: 8),
                  GlassBadge(
                    label: preview.isExpired ? 'Invite Expired' : 'Invite Already Used',
                    tint: AppTheme.stateWarning,
                    icon: Icons.warning_amber_rounded,
                  ),
                ],
                if (preview.topGenres.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Text('Top Genres', style: textTheme.bodySmall),
                  const SizedBox(height: 6),
                  Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: preview.topGenres
                        .map((genre) => GlassBadge(label: genre, tint: AppTheme.primaryViolet))
                        .toList(),
                  ),
                ],
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    icon: _isAccepting
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(Icons.check_circle_outline),
                    label: Text(_isAccepting ? 'Accepting…' : 'Accept Invite'),
                    onPressed: (canAccept && !_isAccepting) ? _acceptInvite : null,
                  ),
                ),
              ],
            ),
          ),
        ],
        if (_acceptError != null) ...[
          const SizedBox(height: 8),
          _buildErrorBanner(_acceptError!),
        ],
      ],
    );
  }

  Widget _buildErrorBanner(String message) {
    return GlassErrorState(
      message: message,
      margin: EdgeInsets.zero,
    );
  }
}
