// CineVault OS — Glass Badge
//
// Small tinted pill (ratings, trust tiers, status chips), mirroring web's
// low-opacity accent-wash badges (e.g. `bg-amber-500/15 border-amber-500/30`).
// Deliberately no blur — see GlassContainer's GlassBlurTier doc.

import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/theme/glass_tokens.dart';

class GlassBadge extends StatelessWidget {
  const GlassBadge({
    super.key,
    required this.label,
    this.tint = AppTheme.primaryViolet,
    this.icon,
    this.fillOpacity,
    this.borderOpacity,
  });

  final String label;
  final Color tint;
  final IconData? icon;

  /// Override the default translucent fill (GlassTokens.badgeFillOpacity)
  /// for a higher-contrast badge — e.g. a label a curator relies on to
  /// identify a data source, where the default 15% wash reads as barely
  /// visible against a busy background.
  final double? fillOpacity;
  final double? borderOpacity;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: tint.withValues(alpha: fillOpacity ?? GlassTokens.badgeFillOpacity),
        borderRadius: BorderRadius.circular(GlassTokens.radiusPill),
        border: Border.all(color: tint.withValues(alpha: borderOpacity ?? GlassTokens.badgeBorderOpacity)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 12, color: tint),
            const SizedBox(width: 4),
          ],
          Flexible(
            child: Text(
              label,
              overflow: TextOverflow.ellipsis,
              maxLines: 1,
              style: TextStyle(color: tint, fontSize: 11, fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }
}
