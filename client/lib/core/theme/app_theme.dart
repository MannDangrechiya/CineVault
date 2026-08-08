// CineVault OS — Accessible Premium Dark Design System
// Tailored color palette, high contrast, smooth transitions, scalable typography, and accessible tap targets

import 'package:flutter/material.dart';

class AppTheme {
  // Brand Color Tokens
  static const Color primaryViolet = Color(0xFF7C4DFF);
  static const Color primaryLightViolet = Color(0xFFB388FF);
  static const Color secondaryCyan = Color(0xFF00E5FF);
  static const Color accentGold = Color(0xFFFFD700);

  // Background & Surface Tokens
  static const Color darkBackground = Color(0xFF0D0E15);
  static const Color cardSurface = Color(0xFF161824);
  static const Color cardElevated = Color(0xFF1F2234);
  static const Color borderSubtle = Color(0xFF2A2D43);

  // Text Tokens (High Contrast WCAG AAA/AA)
  static const Color textPrimary = Color(0xFFF0F2F8);
  static const Color textSecondary = Color(0xFFA0A7C2);
  static const Color textMuted = Color(0xFF6C728E);

  // State Tokens
  static const Color stateSuccess = Color(0xFF00E676);
  static const Color stateWarning = Color(0xFFFF9100);
  static const Color stateError = Color(0xFFFF1744);
  static const Color stateInfo = Color(0xFF29B6F6);

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: darkBackground,
      colorScheme: const ColorScheme.dark(
        primary: primaryViolet,
        secondary: secondaryCyan,
        tertiary: accentGold,
        surface: cardSurface,
        background: darkBackground,
        error: stateError,
        onPrimary: Colors.white,
        onSecondary: Colors.black,
        onSurface: textPrimary,
        onError: Colors.white,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: cardSurface,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          color: textPrimary,
          fontSize: 20,
          fontWeight: FontWeight.bold,
          letterSpacing: 0.5,
        ),
        iconTheme: IconThemeData(color: textPrimary),
      ),
      cardTheme: CardThemeData(
        color: cardSurface,
        elevation: 4,
        shadowColor: Colors.black.withOpacity(0.4),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: borderSubtle, width: 1),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primaryViolet,
          foregroundColor: Colors.white,
          minimumSize: const Size(88, 48), // Accessible 48px tap target
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.3,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: primaryLightViolet,
          minimumSize: const Size(88, 48),
          side: const BorderSide(color: primaryViolet, width: 1.5),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: cardElevated,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: borderSubtle),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: borderSubtle),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: primaryViolet, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: stateError),
        ),
        hintStyle: const TextStyle(color: textMuted, fontSize: 14),
        labelStyle: const TextStyle(color: textSecondary, fontSize: 14),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: cardSurface,
        selectedItemColor: primaryLightViolet,
        unselectedItemColor: textMuted,
        type: BottomNavigationBarType.fixed,
        elevation: 8,
      ),
      textTheme: const TextTheme(
        headlineLarge: TextStyle(color: textPrimary, fontSize: 28, fontWeight: FontWeight.bold, letterSpacing: -0.5),
        headlineMedium: TextStyle(color: textPrimary, fontSize: 22, fontWeight: FontWeight.bold),
        titleLarge: TextStyle(color: textPrimary, fontSize: 18, fontWeight: FontWeight.w600),
        titleMedium: TextStyle(color: textPrimary, fontSize: 16, fontWeight: FontWeight.w500),
        bodyLarge: TextStyle(color: textPrimary, fontSize: 16, height: 1.4),
        bodyMedium: TextStyle(color: textSecondary, fontSize: 14, height: 1.4),
        bodySmall: TextStyle(color: textMuted, fontSize: 12),
      ),
    );
  }
}
