// CineVault OS — Glass Bottom Nav
//
// A frosted bottom navigation bar: real BackdropFilter blur over whatever
// scrolls behind it. Pair with `Scaffold(extendBody: true)` so page content
// is visible (and blurred) underneath it.

import 'dart:ui';
import 'package:flutter/material.dart';
import '../../../core/theme/glass_tokens.dart';

class GlassBottomNav extends StatelessWidget {
  const GlassBottomNav({
    super.key,
    required this.currentIndex,
    required this.onTap,
    required this.items,
  });

  final int currentIndex;
  final ValueChanged<int> onTap;
  final List<BottomNavigationBarItem> items;

  @override
  Widget build(BuildContext context) {
    return ClipRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: GlassTokens.blurXl, sigmaY: GlassTokens.blurXl),
        child: Container(
          decoration: BoxDecoration(
            color: GlassTokens.surfaceTint.withValues(alpha: GlassTokens.surfaceOpacityHigh),
            border: const Border(top: BorderSide(color: GlassTokens.borderHairline)),
          ),
          child: SafeArea(
            top: false,
            child: BottomNavigationBar(
              currentIndex: currentIndex,
              onTap: onTap,
              items: items,
              backgroundColor: Colors.transparent,
              elevation: 0,
              type: BottomNavigationBarType.fixed,
            ),
          ),
        ),
      ),
    );
  }
}
