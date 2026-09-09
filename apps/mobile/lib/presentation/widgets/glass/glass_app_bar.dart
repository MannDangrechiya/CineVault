// CineVault OS — Glass App Bar
//
// A frosted top bar: real BackdropFilter blur over whatever scrolls behind
// it. Pair with `Scaffold(extendBodyBehindAppBar: true)` so there is content
// behind it to blur — on a flat background this reads as a plain
// translucent rectangle.

import 'dart:ui';
import 'package:flutter/material.dart';
import '../../../core/theme/glass_tokens.dart';

class GlassAppBar extends StatelessWidget implements PreferredSizeWidget {
  const GlassAppBar({
    super.key,
    this.title,
    this.actions,
    this.leading,
    this.centerTitle = false,
    this.automaticallyImplyLeading = true,
  });

  final Widget? title;
  final List<Widget>? actions;
  final Widget? leading;
  final bool centerTitle;
  final bool automaticallyImplyLeading;

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);

  /// The vertical space this app bar occupies (status bar + toolbar).
  ///
  /// `GlassAppBar` is meant to float over content (`extendBodyBehindAppBar:
  /// true`), so — unlike a normal `AppBar` in a non-extended `Scaffold` — it
  /// reserves no layout space for itself. A screen whose body should NOT
  /// bleed under the translucent bar needs a matching spacer as its body's
  /// first child; use this instead of hand-rolling
  /// `MediaQuery.of(context).padding.top + kToolbarHeight` at each call site.
  static Widget contentSpacer(BuildContext context) {
    return SizedBox(height: MediaQuery.of(context).padding.top + kToolbarHeight);
  }

  @override
  Widget build(BuildContext context) {
    return ClipRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: GlassTokens.blurXl, sigmaY: GlassTokens.blurXl),
        child: Container(
          decoration: BoxDecoration(
            color: GlassTokens.surfaceTint.withValues(alpha: GlassTokens.surfaceOpacityHigh),
            border: const Border(bottom: BorderSide(color: GlassTokens.borderHairline)),
          ),
          child: SafeArea(
            bottom: false,
            child: AppBar(
              title: title,
              actions: actions,
              leading: leading,
              centerTitle: centerTitle,
              automaticallyImplyLeading: automaticallyImplyLeading,
              backgroundColor: Colors.transparent,
              elevation: 0,
              scrolledUnderElevation: 0,
            ),
          ),
        ),
      ),
    );
  }
}
