// CineVault OS — Title Detail Screen (8.1, 8.2, 8.6, 8.7)
// Displays canonical title metadata, streaming availability (8.6), similar titles (8.7), and watch event logger (8.2)
// Also hosts the personal rating/note/review UI (Part 3 personal domain).

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../domain/entities/personal.dart';
import '../../domain/entities/title.dart';
import '../providers/catalog_provider.dart';
import '../providers/personal_provider.dart';
import '../providers/recommendation_provider.dart';
import '../providers/sync_provider.dart';
import '../widgets/glass/glass.dart';

class TitleDetailScreen extends ConsumerStatefulWidget {
  final String titleId;

  const TitleDetailScreen({super.key, required this.titleId});

  @override
  ConsumerState<TitleDetailScreen> createState() => _TitleDetailScreenState();
}

class _TitleDetailScreenState extends ConsumerState<TitleDetailScreen> {
  // ── Rating (8.2 personal domain) ────────────────────────────────────
  // NOTE: PersonalRemoteDatasource exposes no GET-by-title lookup for an
  // existing rating (only setRating), so this always starts unrated (0)
  // on screen entry rather than reflecting a rating saved on a previous
  // visit. Picking a value still overwrites the backend rating via
  // setRating() — it just isn't pre-filled here.
  int _selectedRating = 0;
  bool _isSubmittingRating = false;

  // ── Private note ─────────────────────────────────────────────────────
  final _noteController = TextEditingController();
  bool _isSavingNote = false;

  // ── Reviews ──────────────────────────────────────────────────────────
  List<ReviewEntity> _reviews = const [];
  bool _isLoadingReviews = false;
  String? _reviewsError;

  @override
  void initState() {
    super.initState();
    _fetchReviews();
  }

  @override
  void dispose() {
    _noteController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final titleAsync = ref.watch(titleDetailProvider(widget.titleId));
    final availabilityAsync = ref.watch(titleAvailabilityProvider(widget.titleId));
    final similarAsync = ref.watch(similarTitlesProvider(widget.titleId));
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: const GlassAppBar(title: Text('Title Details')),
      body: titleAsync.when(
        loading: () => const Center(
          child: CircularProgressIndicator(
            semanticsLabel: 'Loading title details',
          ),
        ),
        error: (err, _) => Center(
          child: Text(
            'Error loading details: $err',
            style: textTheme.bodyLarge,
          ),
        ),
        data: (title) {
          return SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _HeroSection(title: title, textTheme: textTheme),
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Action Buttons (Watch Log & Rating)
                      Row(
                        children: [
                          Expanded(
                            child: ElevatedButton.icon(
                              icon: const Icon(Icons.bookmark_add),
                              label: const Text('Log Watch Event'),
                              onPressed: () => _showWatchLogDialog(
                                title.titleId,
                                title.primaryTitle,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),

                      // Availability Domain Section (8.6)
                      Text(
                        'Streaming & Platform Availability (8.6)',
                        style: textTheme.titleLarge,
                      ),
                      const SizedBox(height: 8),
                      availabilityAsync.when(
                        loading: () => const LinearProgressIndicator(),
                        error: (_, __) => const Text(
                          'Availability data unavailable.',
                          style: TextStyle(color: AppTheme.textMuted),
                        ),
                        data: (availabilities) {
                          if (availabilities.isEmpty) {
                            return const Text(
                              'No active streaming releases found.',
                              style: TextStyle(color: AppTheme.textMuted),
                            );
                          }
                          return Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: availabilities.map((avail) {
                              return GlassBadge(
                                label:
                                    '${avail.platformName} (${avail.offerType})',
                                icon: Icons.play_circle_fill,
                                tint: AppTheme.secondaryCyan,
                              );
                            }).toList(),
                          );
                        },
                      ),
                      const SizedBox(height: 24),

                      // Personal Domain Section — Rating, Note & Reviews (8.2)
                      Text(
                        'Your Rating & Notes',
                        style: textTheme.titleLarge,
                      ),
                      const SizedBox(height: 8),
                      _buildRatingAndNoteCard(title.titleId, textTheme),
                      const SizedBox(height: 20),
                      _buildReviewsSection(title.titleId, textTheme),
                      const SizedBox(height: 24),

                      // Recommendations / Similar Titles (8.7)
                      Text(
                        'Similar Titles (8.7 Recommendation Engine)',
                        style: textTheme.titleLarge,
                      ),
                      const SizedBox(height: 8),
                      similarAsync.when(
                        loading: () => const LinearProgressIndicator(),
                        error: (_, __) => const Text(
                          'Similar titles unavailable.',
                          style: TextStyle(color: AppTheme.textMuted),
                        ),
                        data: (similarItems) {
                          if (similarItems.isEmpty) {
                            return const Text(
                              'No content-similar candidates generated.',
                              style: TextStyle(color: AppTheme.textMuted),
                            );
                          }
                          return Column(
                            children: similarItems.map((sim) {
                              return GlassCard(
                                margin: const EdgeInsets.only(bottom: 8),
                                onTap: () {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) => TitleDetailScreen(
                                        titleId: sim.titleId,
                                      ),
                                    ),
                                  );
                                },
                                child: ListTile(
                                  contentPadding: EdgeInsets.zero,
                                  leading: const Icon(
                                    Icons.movie_outlined,
                                    color: AppTheme.primaryLightViolet,
                                  ),
                                  title: Text(
                                    sim.titleName,
                                    style: textTheme.titleMedium,
                                  ),
                                  subtitle: Text(
                                    'Score: ${(sim.recommendationScore * 100).toStringAsFixed(1)}% | ${sim.groundedExplanation.explanationText}',
                                  ),
                                ),
                              );
                            }).toList(),
                          );
                        },
                      ),
                    ],
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  // ── Rating & private note ───────────────────────────────────────────

  Widget _buildRatingAndNoteCard(String titleId, TextTheme textTheme) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Rate this title', style: textTheme.titleMedium),
          const SizedBox(height: 4),
          Text(
            _selectedRating == 0
                ? 'Tap a number to rate (1-10)'
                : 'Your rating: $_selectedRating / 10',
            style: textTheme.bodySmall,
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: List.generate(10, (index) {
              final value = index + 1;
              final isSelected = value == _selectedRating;
              return ChoiceChip(
                label: Text('$value'),
                selected: isSelected,
                showCheckmark: false,
                onSelected: _isSubmittingRating
                    ? null
                    : (_) => _submitRating(titleId, value),
                labelStyle: TextStyle(
                  color: isSelected ? AppTheme.accentGold : AppTheme.textSecondary,
                  fontWeight: FontWeight.w600,
                ),
                backgroundColor: AppTheme.cardElevated,
                selectedColor: AppTheme.accentGold.withValues(alpha: 0.2),
                side: BorderSide(
                  color: isSelected ? AppTheme.accentGold : AppTheme.borderSubtle,
                ),
              );
            }),
          ),
          const Divider(height: 32, color: AppTheme.borderSubtle),
          Text('Private Note', style: textTheme.titleMedium),
          const SizedBox(height: 8),
          TextFormField(
            controller: _noteController,
            maxLines: 4,
            decoration: const InputDecoration(
              hintText: 'Jot down private thoughts about this title…',
            ),
          ),
          const SizedBox(height: 8),
          Align(
            alignment: Alignment.centerRight,
            child: ElevatedButton.icon(
              onPressed: _isSavingNote ? null : () => _saveNote(titleId),
              icon: _isSavingNote
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Icon(Icons.save_outlined),
              label: const Text('Save Note'),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _submitRating(String titleId, int value) async {
    setState(() => _isSubmittingRating = true);
    try {
      await ref
          .read(personalRemoteDatasourceProvider)
          .setRating(titleId: titleId, ratingValue: value);
      if (!mounted) return;
      setState(() => _selectedRating = value);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Rating saved: $value / 10')),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to save rating: $e')),
      );
    } finally {
      if (mounted) setState(() => _isSubmittingRating = false);
    }
  }

  Future<void> _saveNote(String titleId) async {
    final noteText = _noteController.text.trim();
    if (noteText.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Write something before saving your note.'),
        ),
      );
      return;
    }
    setState(() => _isSavingNote = true);
    try {
      await ref
          .read(personalRemoteDatasourceProvider)
          .upsertNote(titleId: titleId, noteText: noteText);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Note saved')),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to save note: $e')),
      );
    } finally {
      if (mounted) setState(() => _isSavingNote = false);
    }
  }

  // ── Reviews ──────────────────────────────────────────────────────────

  Widget _buildReviewsSection(String titleId, TextTheme textTheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text('Reviews', style: textTheme.titleLarge),
            const Spacer(),
            OutlinedButton.icon(
              icon: const Icon(Icons.rate_review_outlined, size: 18),
              label: const Text('Write a Review'),
              onPressed: () => _showWriteReviewDialog(titleId),
            ),
          ],
        ),
        const SizedBox(height: 8),
        if (_isLoadingReviews)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 8),
            child: LinearProgressIndicator(),
          )
        else if (_reviewsError != null)
          Text(
            _reviewsError!,
            style: const TextStyle(color: AppTheme.stateError),
          )
        else if (_reviews.isEmpty)
          const Text(
            'No reviews yet. Be the first to share your thoughts.',
            style: TextStyle(color: AppTheme.textMuted),
          )
        else
          Column(
            children: _reviews.map((review) {
              final hasTitle = (review.reviewTitle ?? '').trim().isNotEmpty;
              return GlassCard(
                margin: const EdgeInsets.only(bottom: 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: Text(
                            hasTitle ? review.reviewTitle! : 'Untitled review',
                            style: textTheme.titleMedium,
                          ),
                        ),
                        const SizedBox(width: 8),
                        GlassBadge(
                          label: review.isPublic ? 'Public' : 'Private',
                          icon: review.isPublic
                              ? Icons.public
                              : Icons.lock_outline,
                          tint: review.isPublic
                              ? AppTheme.secondaryCyan
                              : AppTheme.textMuted,
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(review.reviewText, style: textTheme.bodyMedium),
                  ],
                ),
              );
            }).toList(),
          ),
      ],
    );
  }

  Future<void> _fetchReviews() async {
    setState(() {
      _isLoadingReviews = true;
      _reviewsError = null;
    });
    try {
      final reviews = await ref
          .read(personalRemoteDatasourceProvider)
          .getUserReviews(titleId: widget.titleId);
      if (!mounted) return;
      setState(() => _reviews = reviews);
    } catch (e) {
      if (!mounted) return;
      setState(() => _reviewsError = 'Failed to load reviews: $e');
    } finally {
      if (mounted) setState(() => _isLoadingReviews = false);
    }
  }

  Future<void> _showWriteReviewDialog(String titleId) async {
    final reviewTitleController = TextEditingController();
    final reviewTextController = TextEditingController();
    final formKey = GlobalKey<FormState>();
    bool isPublic = true;
    bool isSubmitting = false;

    await GlassModalSheet.showDialogPanel(
      context: context,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (dialogContext, setDialogState) {
            return Padding(
              padding: const EdgeInsets.all(20.0),
              child: Form(
                key: formKey,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Text(
                      'Write a Review',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: reviewTitleController,
                      autofocus: true,
                      decoration: const InputDecoration(labelText: 'Review title'),
                      validator: (value) => (value == null || value.trim().isEmpty)
                          ? 'Title is required'
                          : null,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: reviewTextController,
                      decoration: const InputDecoration(labelText: 'Your review'),
                      maxLines: 5,
                      validator: (value) => (value == null || value.trim().isEmpty)
                          ? 'Review text is required'
                          : null,
                    ),
                    const SizedBox(height: 4),
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('Public review'),
                      subtitle: Text(
                        isPublic ? 'Visible to other users' : 'Only visible to you',
                      ),
                      value: isPublic,
                      onChanged: isSubmitting
                          ? null
                          : (value) => setDialogState(() => isPublic = value),
                    ),
                    const SizedBox(height: 12),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        TextButton(
                          onPressed: isSubmitting
                              ? null
                              : () => Navigator.pop(dialogContext),
                          child: const Text('Cancel'),
                        ),
                        const SizedBox(width: 8),
                        ElevatedButton(
                          onPressed: isSubmitting
                              ? null
                              : () => _submitReview(
                                    dialogContext: dialogContext,
                                    setSubmitting: (value) =>
                                        setDialogState(() => isSubmitting = value),
                                    formKey: formKey,
                                    titleId: titleId,
                                    reviewTitleController: reviewTitleController,
                                    reviewTextController: reviewTextController,
                                    isPublic: isPublic,
                                  ),
                          child: isSubmitting
                              ? const SizedBox(
                                  width: 18,
                                  height: 18,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white,
                                  ),
                                )
                              : const Text('Submit'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );

    reviewTitleController.dispose();
    reviewTextController.dispose();
  }

  Future<void> _submitReview({
    required BuildContext dialogContext,
    required void Function(bool) setSubmitting,
    required GlobalKey<FormState> formKey,
    required String titleId,
    required TextEditingController reviewTitleController,
    required TextEditingController reviewTextController,
    required bool isPublic,
  }) async {
    if (!(formKey.currentState?.validate() ?? false)) return;
    setSubmitting(true);
    try {
      await ref.read(personalRemoteDatasourceProvider).createUserReview(
            titleId: titleId,
            reviewTitle: reviewTitleController.text.trim(),
            reviewText: reviewTextController.text.trim(),
            isPublic: isPublic,
          );
      if (dialogContext.mounted) Navigator.pop(dialogContext);
      await _fetchReviews();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Review submitted')),
      );
    } catch (e) {
      if (!dialogContext.mounted) return;
      setSubmitting(false);
      ScaffoldMessenger.of(dialogContext).showSnackBar(
        SnackBar(content: Text('Failed to submit review: $e')),
      );
    }
  }

  // ── Watch log dialog (8.2) ──────────────────────────────────────────

  void _showWatchLogDialog(String titleId, String titleName) {
    double progressPercentage = 100.0;

    showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          title: Text('Log Watch Event for $titleName'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<double>(
                initialValue: progressPercentage,
                decoration: const InputDecoration(labelText: 'Watch Progress'),
                items: const [
                  DropdownMenuItem(
                    value: 100.0,
                    child: Text('Completed (100%)'),
                  ),
                  DropdownMenuItem(value: 75.0, child: Text('75%')),
                  DropdownMenuItem(value: 50.0, child: Text('50%')),
                  DropdownMenuItem(value: 25.0, child: Text('25%')),
                ],
                onChanged: (val) => progressPercentage = val ?? 100.0,
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () {
                ref
                    .read(syncProvider.notifier)
                    .queueAndSync(
                      mutationType: 'CREATE_WATCH_EVENT',
                      payload: {
                        'title_id': titleId,
                        'watched_at': DateTime.now().toUtc().toIso8601String(),
                        'progress_percentage': progressPercentage,
                      },
                    );
                Navigator.pop(ctx);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text(
                      'Watch event queued in local outbox (ADR-004)',
                    ),
                  ),
                );
              },
              child: const Text('Save Event'),
            ),
          ],
        );
      },
    );
  }
}

/// Hero banner: the backdrop (or poster) image shown in full, with a frosted
/// glass panel of title/metadata/synopsis overlapping its bottom edge.
class _HeroSection extends StatelessWidget {
  const _HeroSection({required this.title, required this.textTheme});

  final CanonicalTitleEntity title;
  final TextTheme textTheme;

  @override
  Widget build(BuildContext context) {
    final heroImageUrl =
        (title.backdropUrl != null && title.backdropUrl!.isNotEmpty)
        ? title.backdropUrl
        : title.posterUrl;

    return SizedBox(
      height: 380,
      child: Stack(
        fit: StackFit.expand,
        children: [
          Positioned.fill(
            child: heroImageUrl != null && heroImageUrl.isNotEmpty
                ? Image.network(
                    heroImageUrl,
                    fit: BoxFit.cover,
                    loadingBuilder: (context, child, loadingProgress) {
                      if (loadingProgress == null) return child;
                      return Container(
                        color: AppTheme.cardElevated,
                        child: const Center(
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                      );
                    },
                    errorBuilder: (context, error, stackTrace) => Container(
                      color: AppTheme.cardElevated,
                      child: Center(
                        child: Icon(
                          title.contentType == 'MOVIE' ? Icons.movie : Icons.tv,
                          size: 72,
                          color: AppTheme.primaryLightViolet,
                        ),
                      ),
                    ),
                  )
                : Container(
                    color: AppTheme.cardElevated,
                    child: Center(
                      child: Icon(
                        title.contentType == 'MOVIE' ? Icons.movie : Icons.tv,
                        size: 72,
                        color: AppTheme.primaryLightViolet,
                      ),
                    ),
                  ),
          ),
          // Scrim so the glass panel's text stays legible over bright artwork.
          Positioned.fill(
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  stops: const [0.35, 1.0],
                  colors: [
                    Colors.transparent,
                    Colors.black.withValues(alpha: 0.55),
                  ],
                ),
              ),
            ),
          ),
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: GlassContainer(
              blurTier: GlassBlurTier.xl,
              borderRadius: const BorderRadius.vertical(
                top: Radius.circular(GlassTokens.radiusLg),
              ),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(title.primaryTitle, style: textTheme.headlineMedium),
                  if (title.originalTitle != null) ...[
                    const SizedBox(height: 4),
                    Text(
                      'Original: ${title.originalTitle}',
                      style: textTheme.bodySmall,
                    ),
                  ],
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      GlassBadge(
                        label: title.contentType,
                        tint: AppTheme.primaryViolet,
                      ),
                      if (title.releaseYear != null) ...[
                        const SizedBox(width: 8),
                        GlassBadge(
                          label: '${title.releaseYear}',
                          tint: AppTheme.accentGold,
                        ),
                      ],
                    ],
                  ),
                  const SizedBox(height: 16),
                  Text('Synopsis', style: textTheme.titleLarge),
                  const SizedBox(height: 8),
                  Text(
                    title.overview ??
                        'No overview available for this canonical title.',
                    style: textTheme.bodyLarge,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
