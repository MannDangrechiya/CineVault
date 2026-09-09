// CineVault OS — Glass Design Tokens
//
// Blur tiers, translucent surface tints, hairline borders, and radii that
// mirror the web app's glassmorphism system (backdrop-blur-sm/md/xl over a
// zinc/violet OLED dark theme). See apps/web/src/components/layout/Header.tsx,
// Sidebar.tsx, src/components/ui/States.tsx, TitleCard.tsx for the reference.
//
// These extend AppTheme's color tokens — they don't replace them. Buttons,
// inputs, and text keep AppTheme's solid styling, exactly like web keeps
// solid buttons alongside its glass chrome/cards.

import 'package:flutter/material.dart';
import 'app_theme.dart';

class GlassTokens {
  GlassTokens._();

  // Blur sigma tiers (dart:ui ImageFilter.blur), scaling with prominence
  // like web's backdrop-blur-sm/md/xl. Reserved for singleton chrome (app
  // bar, bottom nav, modal sheets, hero panels) — BackdropFilter forces an
  // expensive saveLayer/blur pass per instance, so never apply it per-item
  // inside a scrolling ListView/GridView (use GlassCard's tint-only look
  // there instead).
  static const double blurSm = 4.0;
  static const double blurMd = 12.0;
  static const double blurXl = 24.0;

  // Translucent surface tint + opacity tiers, mirroring web's
  // zinc-900/30–70 and black/80–85 panels.
  static const Color surfaceTint = AppTheme.cardSurface;
  static const double surfaceOpacityLow = 0.30;
  static const double surfaceOpacityMid = 0.50;
  static const double surfaceOpacityHigh = 0.70;

  // Modal/dialog scrim opacity (web: bg-black/80–85).
  static const double scrimOpacity = 0.82;

  // Hairline border — AppTheme.borderSubtle (#2A2D43) at ~20% alpha.
  static const Color borderHairline = Color(0x332A2D43);

  // Radius scale mirroring Tailwind rounded-xl/2xl/3xl.
  static const double radiusMd = 12.0;
  static const double radiusLg = 16.0;
  static const double radiusXl = 24.0;
  static const double radiusPill = 999.0;

  /// Tinted-badge alpha pair (fill, border) matching web's
  /// `bg-<hue>-500/15 border-<hue>-500/30`-style low-opacity accent washes.
  static const double badgeFillOpacity = 0.15;
  static const double badgeBorderOpacity = 0.35;
}
