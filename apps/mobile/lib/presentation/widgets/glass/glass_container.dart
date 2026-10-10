// CineVault OS — Glass Container
//
// Base glassmorphism primitive: a translucent, hairline-bordered surface,
// optionally blurred (BackdropFilter) against whatever sits behind it.
// Every other glass widget in this directory builds on this one.

import 'dart:ui';
import 'package:flutter/material.dart';
import '../../../core/theme/glass_tokens.dart';

/// How strongly this surface blurs the content behind it.
///
/// [none] renders a cheap translucent tint with no BackdropFilter — use this
/// for anything repeated in a list/grid (see GlassCard). The blurred tiers
/// are for singleton chrome only (app bar, bottom nav, modal sheets, hero
/// panels): a BackdropFilter forces a saveLayer/blur pass per instance and
/// will jank a scrolling list if applied per-item.
enum GlassBlurTier { none, sm, md, xl }

class GlassContainer extends StatelessWidget {
  const GlassContainer({
    super.key,
    required this.child,
    this.blurTier = GlassBlurTier.md,
    this.tintColor,
    this.tintOpacity,
    this.borderRadius = const BorderRadius.all(Radius.circular(GlassTokens.radiusLg)),
    this.borderColor,
    this.padding,
    this.margin,
  });

  final Widget child;
  final GlassBlurTier blurTier;
  final Color? tintColor;
  final double? tintOpacity;
  final BorderRadius borderRadius;
  final Color? borderColor;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;

  double get _sigma {
    switch (blurTier) {
      case GlassBlurTier.none:
        return 0;
      case GlassBlurTier.sm:
        return GlassTokens.blurSm;
      case GlassBlurTier.md:
        return GlassTokens.blurMd;
      case GlassBlurTier.xl:
        return GlassTokens.blurXl;
    }
  }

  BoxDecoration _decoration() {
    return BoxDecoration(
      color: (tintColor ?? GlassTokens.surfaceTint)
          .withValues(alpha: tintOpacity ?? GlassTokens.surfaceOpacityMid),
      borderRadius: borderRadius,
      border: Border.all(color: borderColor ?? GlassTokens.borderHairline),
    );
  }

  @override
  Widget build(BuildContext context) {
    // Always clipped to borderRadius, even without blur — otherwise a
    // zero-padding child (an image, a future ink effect) can paint past the
    // rounded corners on a tint-only (GlassBlurTier.none) surface.
    final clippedSurface = ClipRRect(
      borderRadius: borderRadius,
      child: Container(
        padding: padding,
        decoration: _decoration(),
        child: child,
      ),
    );

    final result = blurTier == GlassBlurTier.none
        ? clippedSurface
        : ClipRRect(
            borderRadius: borderRadius,
            child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: _sigma, sigmaY: _sigma),
              child: clippedSurface,
            ),
          );

    return margin == null ? result : Padding(padding: margin!, child: result);
  }
}
