// CineVault OS — Swipe Discovery Screen (Modern Dating-App Style 4-Way Gestures)
// Swipe Right: Mark Watched | Swipe Left: Pass | Swipe Up: Add to Watchlist | Swipe Down: Detailed Info

import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../domain/entities/title.dart';
import '../providers/catalog_provider.dart';
import '../providers/sync_provider.dart';
import 'title_detail_screen.dart';

enum SwipeDirection { left, right, up, down, none }

class SwipeDiscoveryScreen extends ConsumerStatefulWidget {
  const SwipeDiscoveryScreen({super.key});

  @override
  ConsumerState<SwipeDiscoveryScreen> createState() => _SwipeDiscoveryScreenState();
}

class _SwipeDiscoveryScreenState extends ConsumerState<SwipeDiscoveryScreen>
    with SingleTickerProviderStateMixin {
  int _currentIndex = 0;
  Offset _dragOffset = Offset.zero;
  bool _isDragging = false;
  
  // History stack for Undo action
  final List<CanonicalTitleEntity> _swipedHistory = [];

  @override
  Widget build(BuildContext context) {
    final catalogState = ref.watch(catalogProvider);
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.style, color: AppTheme.accentGold),
            SizedBox(width: 8),
            Text('Swipe Discover'),
          ],
        ),
        actions: [
          if (_swipedHistory.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.undo),
              tooltip: 'Undo last swipe',
              onPressed: _undoLastSwipe,
            ),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Stack',
            onPressed: () {
              setState(() {
                _currentIndex = 0;
                _swipedHistory.clear();
              });
              ref.read(catalogProvider.notifier).fetchTitles();
            },
          ),
        ],
      ),
      body: catalogState.isLoading
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(color: AppTheme.primaryViolet),
                  SizedBox(height: 16),
                  Text('Loading cards for discovery deck...'),
                ],
              ),
            )
          : catalogState.titles.isEmpty
              ? Center(
                  child: Text('No titles available to swipe.', style: textTheme.bodyLarge),
                )
              : _currentIndex >= catalogState.titles.length
                  ? _buildCompletedDeckView(context)
                  : _buildCardStack(context, catalogState.titles),
    );
  }

  Widget _buildCompletedDeckView(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.check_circle_outline, size: 80, color: AppTheme.secondaryCyan),
            const SizedBox(height: 16),
            Text(
              'Deck Completed!',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            const Text(
              'You have swiped through all available titles in your catalog. Pull new titles or reset the deck below.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppTheme.textMuted),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              icon: const Icon(Icons.replay),
              label: const Text('Start Deck Over'),
              onPressed: () {
                setState(() {
                  _currentIndex = 0;
                  _swipedHistory.clear();
                });
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCardStack(BuildContext context, List<CanonicalTitleEntity> titles) {
    final currentTitle = titles[_currentIndex];
    final nextTitle = _currentIndex + 1 < titles.length ? titles[_currentIndex + 1] : null;

    return Column(
      children: [
        // Direction Guide Legend Header
        Container(
          padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
          color: AppTheme.cardSurface,
          child: const Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _GuideChip(icon: Icons.arrow_back, label: '👈 Pass', color: Colors.redAccent),
              _GuideChip(icon: Icons.arrow_upward, label: '👆 Watchlist', color: Colors.amber),
              _GuideChip(icon: Icons.arrow_downward, label: '👇 Details', color: Colors.cyan),
              _GuideChip(icon: Icons.arrow_forward, label: '👉 Watched', color: Colors.greenAccent),
            ],
          ),
        ),
        const SizedBox(height: 12),

        // Interactive Card Stack Area
        Expanded(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: Stack(
              clipBehavior: Clip.none,
              children: [
                // Background Next Card Preview
                if (nextTitle != null)
                  Positioned.fill(
                    child: Transform.scale(
                      scale: 0.94,
                      child: Opacity(
                        opacity: 0.6,
                        child: _buildTitleCard(context, nextTitle, isTop: false),
                      ),
                    ),
                  ),

                // Top Active Draggable Card
                Positioned.fill(
                  child: GestureDetector(
                    onPanStart: (_) {
                      setState(() {
                        _isDragging = true;
                      });
                    },
                    onPanUpdate: (details) {
                      setState(() {
                        _dragOffset += details.delta;
                      });
                    },
                    onPanEnd: (details) {
                      _handlePanEnd(details, currentTitle);
                    },
                    child: AnimatedContainer(
                      duration: _isDragging ? Duration.zero : const Duration(milliseconds: 250),
                      curve: Curves.easeOut,
                      transform: Matrix4.translationValues(_dragOffset.dx, _dragOffset.dy, 0.0)
                        ..rotateZ(_dragOffset.dx / 1000 * (math.pi / 12)),
                      alignment: Alignment.center,
                      child: Stack(
                        children: [
                          _buildTitleCard(context, currentTitle, isTop: true),

                          // Swipe Overlay Badges
                          _buildSwipeBadges(),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),

        const SizedBox(height: 16),

        // Modern Interactive Action Buttons Toolbar
        _buildActionButtons(context, currentTitle),
        const SizedBox(height: 16),
      ],
    );
  }

  Widget _buildSwipeBadges() {
    final direction = _getSwipeDirection();

    if (direction == SwipeDirection.right) {
      return Positioned(
        top: 40,
        left: 20,
        child: Transform.rotate(
          angle: -math.pi / 12,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              border: Border.all(color: Colors.greenAccent, width: 3),
              borderRadius: BorderRadius.circular(12),
              color: Colors.black.withValues(alpha: 0.7),
            ),
            child: const Row(
              children: [
                Icon(Icons.check_circle, color: Colors.greenAccent, size: 28),
                SizedBox(width: 8),
                Text(
                  'WATCHED',
                  style: TextStyle(
                    color: Colors.greenAccent,
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 2,
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    } else if (direction == SwipeDirection.left) {
      return Positioned(
        top: 40,
        right: 20,
        child: Transform.rotate(
          angle: math.pi / 12,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              border: Border.all(color: Colors.redAccent, width: 3),
              borderRadius: BorderRadius.circular(12),
              color: Colors.black.withValues(alpha: 0.7),
            ),
            child: const Row(
              children: [
                Icon(Icons.close, color: Colors.redAccent, size: 28),
                SizedBox(width: 8),
                Text(
                  'PASS',
                  style: TextStyle(
                    color: Colors.redAccent,
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 2,
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    } else if (direction == SwipeDirection.up) {
      return Positioned(
        bottom: 120,
        left: 0,
        right: 0,
        child: Center(
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
            decoration: BoxDecoration(
              border: Border.all(color: Colors.amber, width: 3),
              borderRadius: BorderRadius.circular(12),
              color: Colors.black.withValues(alpha: 0.8),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.bookmark_add, color: Colors.amber, size: 28),
                SizedBox(width: 8),
                Text(
                  'ADD TO WATCHLIST',
                  style: TextStyle(
                    color: Colors.amber,
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 2,
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    } else if (direction == SwipeDirection.down) {
      return Positioned(
        top: 80,
        left: 0,
        right: 0,
        child: Center(
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
            decoration: BoxDecoration(
              border: Border.all(color: Colors.cyanAccent, width: 3),
              borderRadius: BorderRadius.circular(12),
              color: Colors.black.withValues(alpha: 0.8),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.info_outline, color: Colors.cyanAccent, size: 28),
                SizedBox(width: 8),
                Text(
                  'QUICK DETAILS',
                  style: TextStyle(
                    color: Colors.cyanAccent,
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 2,
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return const SizedBox.shrink();
  }

  SwipeDirection _getSwipeDirection() {
    final dx = _dragOffset.dx;
    final dy = _dragOffset.dy;

    if (dx.abs() > 60 && dx.abs() > dy.abs()) {
      return dx > 0 ? SwipeDirection.right : SwipeDirection.left;
    } else if (dy.abs() > 60 && dy.abs() > dx.abs()) {
      return dy < 0 ? SwipeDirection.up : SwipeDirection.down;
    }
    return SwipeDirection.none;
  }

  void _handlePanEnd(DragEndDetails details, CanonicalTitleEntity title) {
    final direction = _getSwipeDirection();

    if (direction == SwipeDirection.right) {
      _executeSwipe(direction, title, 'Marked as Watched!');
    } else if (direction == SwipeDirection.left) {
      _executeSwipe(direction, title, 'Passed');
    } else if (direction == SwipeDirection.up) {
      _executeSwipe(direction, title, 'Added to Watchlist!');
    } else if (direction == SwipeDirection.down) {
      // Reset drag & open detail screen
      setState(() {
        _dragOffset = Offset.zero;
        _isDragging = false;
      });
      _openDetails(context, title.titleId);
    } else {
      // Snap back if threshold not met
      setState(() {
        _dragOffset = Offset.zero;
        _isDragging = false;
      });
    }
  }

  void _executeSwipe(SwipeDirection direction, CanonicalTitleEntity title, String statusMessage) {
    // Record history for Undo
    _swipedHistory.add(title);

    // Queue mutation action based on direction
    if (direction == SwipeDirection.right) {
      ref.read(syncProvider.notifier).queueAndSync(
        mutationType: 'CREATE_WATCH_EVENT',
        payload: {
          'title_id': title.titleId,
          'watched_at': DateTime.now().toUtc().toIso8601String(),
          'progress_percentage': 100.0,
        },
      );
    } else if (direction == SwipeDirection.up) {
      ref.read(syncProvider.notifier).queueAndSync(
        mutationType: 'ADD_TO_WATCHLIST',
        payload: {
          'title_id': title.titleId,
          'added_at': DateTime.now().toUtc().toIso8601String(),
        },
      );
    }

    ScaffoldMessenger.of(context).hideCurrentSnackBar();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('${title.primaryTitle}: $statusMessage'),
        duration: const Duration(seconds: 1),
        behavior: SnackBarBehavior.floating,
      ),
    );

    // Advance stack index
    setState(() {
      _currentIndex++;
      _dragOffset = Offset.zero;
      _isDragging = false;
    });
  }

  void _undoLastSwipe() {
    if (_swipedHistory.isNotEmpty) {
      final restoredTitle = _swipedHistory.removeLast();
      setState(() {
        if (_currentIndex > 0) {
          _currentIndex--;
        }
        _dragOffset = Offset.zero;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Restored "${restoredTitle.primaryTitle}" to deck'),
          duration: const Duration(seconds: 1),
        ),
      );
    }
  }

  void _openDetails(BuildContext context, String titleId) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => TitleDetailScreen(titleId: titleId),
      ),
    );
  }

  Widget _buildTitleCard(BuildContext context, CanonicalTitleEntity title, {required bool isTop}) {
    return Card(
      elevation: isTop ? 10 : 2,
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Container(
        decoration: const BoxDecoration(
          color: AppTheme.cardSurface,
        ),
        child: Stack(
          children: [
            // Poster Image Background
            Positioned.fill(
              child: title.posterUrl != null && title.posterUrl!.isNotEmpty
                  ? Image.network(
                      title.posterUrl!,
                      fit: BoxFit.cover,
                      errorBuilder: (context, error, stackTrace) => _buildPosterPlaceholder(title),
                    )
                  : _buildPosterPlaceholder(title),
            ),

            // Gradient Overlay for readability
            Positioned.fill(
              child: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      Colors.transparent,
                      Colors.black.withValues(alpha: 0.3),
                      Colors.black.withValues(alpha: 0.85),
                      Colors.black.withValues(alpha: 0.98),
                    ],
                    stops: const [0.0, 0.4, 0.75, 1.0],
                  ),
                ),
              ),
            ),

            // Content Information Layer
            Positioned(
              bottom: 20,
              left: 20,
              right: 20,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Year & Content Type Badge
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppTheme.primaryViolet,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          title.contentType,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      if (title.releaseYear != null)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.2),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            '${title.releaseYear}',
                            style: const TextStyle(color: Colors.white, fontSize: 12),
                          ),
                        ),
                      const Spacer(),
                      const Icon(Icons.star, color: AppTheme.accentGold, size: 18),
                      const SizedBox(width: 4),
                      const Text(
                        '8.5',
                        style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),

                  // Title Name
                  Text(
                    title.primaryTitle,
                    style: const TextStyle(
                      fontSize: 26,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                      height: 1.1,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),

                  // Genre Chips
                  if (title.genres.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(
                      title.genres.join(' • '),
                      style: const TextStyle(color: AppTheme.secondaryCyan, fontSize: 14),
                    ),
                  ],

                  // Overview / Synopsis
                  if (title.overview != null && title.overview!.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    Text(
                      title.overview!,
                      maxLines: 3,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 13,
                        height: 1.3,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPosterPlaceholder(CanonicalTitleEntity title) {
    return Container(
      color: AppTheme.cardElevated,
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              title.contentType == 'MOVIE' ? Icons.movie : Icons.tv,
              size: 80,
              color: AppTheme.primaryLightViolet.withValues(alpha: 0.5),
            ),
            const SizedBox(height: 12),
            Text(
              title.primaryTitle,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionButtons(BuildContext context, CanonicalTitleEntity title) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        // Skip Button
        _ActionButton(
          icon: Icons.close,
          color: Colors.redAccent,
          label: 'Pass',
          onTap: () {
            _executeSwipe(SwipeDirection.left, title, 'Passed');
          },
        ),

        // Info Button
        _ActionButton(
          icon: Icons.info_outline,
          color: Colors.cyanAccent,
          label: 'Details',
          onTap: () {
            _openDetails(context, title.titleId);
          },
        ),

        // Watchlist Button
        _ActionButton(
          icon: Icons.bookmark_add,
          color: Colors.amber,
          label: 'Watchlist',
          onTap: () {
            _executeSwipe(SwipeDirection.up, title, 'Added to Watchlist!');
          },
        ),

        // Watched Button
        _ActionButton(
          icon: Icons.check,
          color: Colors.greenAccent,
          label: 'Watched',
          onTap: () {
            _executeSwipe(SwipeDirection.right, title, 'Marked as Watched!');
          },
        ),
      ],
    );
  }
}

class _GuideChip extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;

  const _GuideChip({required this.icon, required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: color),
        const SizedBox(width: 4),
        Text(
          label,
          style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w600),
        ),
      ],
    );
  }
}

class _ActionButton extends StatelessWidget {
  final IconData icon;
  final Color color;
  final String label;
  final VoidCallback onTap;

  const _ActionButton({
    required this.icon,
    required this.color,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(30),
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppTheme.cardElevated,
              border: Border.all(color: color.withValues(alpha: 0.4), width: 2),
              boxShadow: [
                BoxShadow(
                  color: color.withValues(alpha: 0.15),
                  blurRadius: 10,
                  spreadRadius: 2,
                ),
              ],
            ),
            child: Icon(icon, color: color, size: 28),
          ),
        ),
        const SizedBox(height: 4),
        Text(label, style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
      ],
    );
  }
}
