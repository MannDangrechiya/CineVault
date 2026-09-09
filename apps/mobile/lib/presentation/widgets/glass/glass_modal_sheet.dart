// CineVault OS — Glass Modal Sheet
//
// Bottom-sheet/dialog helpers with a frosted panel (real BackdropFilter
// blur over the page content behind them) and a darkened scrim. The scrim
// itself is a plain translucent barrier rather than a blurred one — Flutter
// has no cheap way to blur a ModalRoute's barrier, and the visible glass
// effect (blurring what's behind the sheet/dialog panel) is what actually
// reads as "glass" to the user.

import 'dart:ui';
import 'package:flutter/material.dart';
import '../../../core/theme/glass_tokens.dart';

class GlassModalSheet {
  GlassModalSheet._();

  static Future<T?> show<T>({
    required BuildContext context,
    required WidgetBuilder builder,
    bool isScrollControlled = false,
  }) {
    return showModalBottomSheet<T>(
      context: context,
      isScrollControlled: isScrollControlled,
      backgroundColor: Colors.transparent,
      barrierColor: Colors.black.withValues(alpha: GlassTokens.scrimOpacity),
      builder: (sheetContext) => ClipRRect(
        borderRadius: const BorderRadius.vertical(top: Radius.circular(GlassTokens.radiusXl)),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: GlassTokens.blurMd, sigmaY: GlassTokens.blurMd),
          child: Container(
            decoration: BoxDecoration(
              color: GlassTokens.surfaceTint.withValues(alpha: GlassTokens.surfaceOpacityHigh),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(GlassTokens.radiusXl)),
              border: Border.all(color: GlassTokens.borderHairline),
            ),
            child: SafeArea(top: false, child: builder(sheetContext)),
          ),
        ),
      ),
    );
  }

  static Future<T?> showDialogPanel<T>({
    required BuildContext context,
    required WidgetBuilder builder,
    bool barrierDismissible = true,
  }) {
    return showDialog<T>(
      context: context,
      barrierDismissible: barrierDismissible,
      barrierColor: Colors.black.withValues(alpha: GlassTokens.scrimOpacity),
      builder: (dialogContext) => Dialog(
        backgroundColor: Colors.transparent,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(GlassTokens.radiusXl),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: GlassTokens.blurMd, sigmaY: GlassTokens.blurMd),
            child: Container(
              decoration: BoxDecoration(
                color: GlassTokens.surfaceTint.withValues(alpha: GlassTokens.surfaceOpacityHigh),
                borderRadius: BorderRadius.circular(GlassTokens.radiusXl),
                border: Border.all(color: GlassTokens.borderHairline),
              ),
              child: builder(dialogContext),
            ),
          ),
        ),
      ),
    );
  }
}
