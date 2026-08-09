// CineVault OS — Client API Configuration Baseline (Phase 9.11)
// Defines server endpoint routes, default timeouts, and Kong API Gateway routing

import 'package:flutter/foundation.dart';

class ApiConfig {
  /// Base API URL resolved by environment and Kong API Gateway settings.
  ///
  /// Selection priority:
  ///   1. Compile-time override via `--dart-define=API_BASE_URL=<url>`
  ///   2. Production release mode → Kong Gateway fronted URL (`https://api.cinevault.org` / `http://localhost:8000`)
  ///   3. Android debug default → `http://10.0.2.2:8000` (standard emulator→host Kong mapping)
  ///   4. Everything else (iOS simulator, desktop, web) → `http://localhost:8000`
  static String get baseUrl {
    const overrideUrl = String.fromEnvironment('API_BASE_URL');
    if (overrideUrl.isNotEmpty) {
      return overrideUrl;
    }

    if (kReleaseMode) {
      return 'https://api.cinevault.org';
    }

    // Android emulator maps 10.0.2.2 → host machine's localhost (Kong Port 8000).
    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000';
    }

    // iOS simulator shares host network; desktop and web use localhost directly via Kong gateway port 8000.
    return 'http://localhost:8000';
  }

  // Timeout settings
  static const Duration connectTimeout = Duration(seconds: 10);
  static const Duration receiveTimeout = Duration(seconds: 15);

  // Endpoints — Auth (9.8)
  static const String loginEndpoint = '/v1/auth/login';

  // Endpoints — Canonical & Discovery (8.1, 8.6)
  static const String titlesEndpoint = '/v1/titles';
  static const String searchEndpoint = '/v1/search';

  // Endpoints — Personal Domain (8.2)
  static const String meLibraryEndpoint = '/v1/me/library';
  static const String watchEventsEndpoint = '/v1/me/watch-events';
  static const String ratingsEndpoint = '/v1/me/ratings';
  static const String reviewsEndpoint = '/v1/me/reviews';
  static const String notesEndpoint = '/v1/me/notes';

  // Endpoints — Recommendation Engine (8.7)
  static const String recommendationsEndpoint = '/v1/recommendations';
  static const String coldStartRecommendationsEndpoint = '/v1/recommendations/cold-start';
  static const String explainRecommendationEndpoint = '/v1/recommendations/explain';

  // Endpoints — AI Assistant (8.8)
  static const String aiAssistantQueryEndpoint = '/v1/ai/assistant/query';
  static const String aiAssistantIntentEndpoint = '/v1/ai/assistant/intent';

  // Endpoints — Offline Sync Protocol (8.9 / ADR-004)
  static const String syncPushEndpoint = '/v1/sync/push';
  static const String syncPullEndpoint = '/v1/sync/pull';
}
