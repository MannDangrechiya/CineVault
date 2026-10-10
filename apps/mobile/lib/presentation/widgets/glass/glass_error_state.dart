// CineVault OS — Glass Error State
// Reusable glass-styled error banner matching the web design system.

import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import 'glass_card.dart';

class GlassErrorState extends StatelessWidget {
  const GlassErrorState({
    super.key,
    required this.message,
    this.title,
    this.onRetry,
    this.margin = const EdgeInsets.all(24),
    this.icon = Icons.error_outline,
  });

  final String message;
  final String? title;
  final VoidCallback? onRetry;
  final EdgeInsetsGeometry margin;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: GlassCard(
        margin: margin,
        tintColor: AppTheme.stateError,
        tintOpacity: 0.15,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(icon, color: AppTheme.stateError),
                const SizedBox(width: 8),
                Flexible(
                  child: Text(
                    message,
                    style: const TextStyle(color: AppTheme.stateError),
                  ),
                ),
              ],
            ),
            if (onRetry != null) ...[
              const SizedBox(height: 12),
              OutlinedButton.icon(
                icon: const Icon(Icons.refresh, size: 16),
                label: const Text('Retry'),
                onPressed: onRetry,
              ),
            ],
          ],
        ),
      ),
    );
  }
}
