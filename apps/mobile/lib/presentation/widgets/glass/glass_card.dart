// CineVault OS — Glass Card
//
// The tint-only (no blur) glass surface for anything repeated in a
// list/grid — catalog tiles, list rows, stat cards. See GlassContainer's
// GlassBlurTier doc for why cards never blur per-instance.

import 'package:flutter/material.dart';
import '../../../core/theme/glass_tokens.dart';
import 'glass_container.dart';

class GlassCard extends StatelessWidget {
  const GlassCard({
    super.key,
    required this.child,
    this.onTap,
    this.padding = const EdgeInsets.all(12),
    this.margin,
    this.tintColor,
    this.tintOpacity,
    this.borderRadius = const BorderRadius.all(Radius.circular(GlassTokens.radiusMd)),
  });

  final Widget child;
  final VoidCallback? onTap;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;
  final Color? tintColor;
  final double? tintOpacity;
  final BorderRadius borderRadius;

  @override
  Widget build(BuildContext context) {
    final card = GlassContainer(
      blurTier: GlassBlurTier.none,
      tintColor: tintColor,
      tintOpacity: tintOpacity,
      borderRadius: borderRadius,
      padding: padding,
      child: child,
    );

    final tappable = onTap == null
        ? card
        : ClipRRect(
            borderRadius: borderRadius,
            child: Material(
              color: Colors.transparent,
              child: InkWell(onTap: onTap, child: card),
            ),
          );

    return margin == null ? tappable : Padding(padding: margin!, child: tappable);
  }
}
