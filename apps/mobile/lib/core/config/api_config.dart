// CineVault OS — Client API Configuration Baseline (Phase 9.11)
// Defines server endpoint routes and default timeouts. Requests go straight
// to Caddy (production) or the local FastAPI dev server — there is no API
// gateway in front of it (Kong was audited and removed in Phase 3).

import 'package:flutter/foundation.dart';

class ApiConfig {
  /// Base API URL resolved by environment.
  ///
  /// Selection priority:
  ///   1. Compile-time override via `--dart-define=API_BASE_URL=<url>`
  ///   2. Production release mode → Caddy-fronted URL (`https://api.cinevault.org`)
  ///   3. Android debug default → `http://127.0.0.1:8000` (host loopback via `adb reverse`)
  ///      For **physical devices**, pass your PC's LAN IP at build time:
  ///        flutter run --dart-define=API_BASE_URL=http://<YOUR_PC_LAN_IP>:8000
  ///   4. Everything else (iOS simulator, desktop, web) → `http://localhost:8000`
  static String get baseUrl {
    const overrideUrl = String.fromEnvironment('API_BASE_URL');
    if (overrideUrl.isNotEmpty) {
      return overrideUrl;
    }

    if (kReleaseMode) {
      return 'https://api.cinevault.org';
    }

    // For Android devices: with `adb reverse tcp:8000 tcp:8000` or local testing, 127.0.0.1 connects to PC server.
    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
      return 'http://127.0.0.1:8000';
    }

    // iOS simulator shares host network; desktop and web use 127.0.0.1 directly.
    return 'http://127.0.0.1:8000';
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

  // Endpoints — Personal Domain: Watchlist, History & Collections (Part 3.4/3.5)
  static const String titleStatesEndpoint = '/v1/me/title-states';
  static const String personalWatchlistEndpoint = '/v1/personal/watchlist';
  static const String personalHistoryEndpoint = '/v1/personal/history';
  static const String personalLibraryEndpoint = '/v1/personal/library';
  static const String personalCollectionsEndpoint = '/v1/personal/collections';
  static const String personalAnalyticsEndpoint = '/v1/personal/analytics';
  static const String personalStreakEndpoint = '/v1/personal/streak';
  static const String personalExportEndpoint = '/v1/personal/export';

  // Endpoints — Social Layer (Part 3.1-3.2, 3.6-3.8): friendships, taste
  // matching, leaderboard, badges, invites/referrals, pick rooms, recap,
  // watch clubs & monthly challenges. See services/api/routers/social.py.
  static const String friendshipsEndpoint = '/social/friendships';
  static const String socialRecommendationsEndpoint = '/social/recommendations';
  static const String tasteMatchesEndpoint = '/social/taste-matches';
  static const String leaderboardEndpoint = '/social/leaderboard';
  static const String badgesEndpoint = '/social/badges';
  static const String invitesEndpoint = '/social/invites';
  static const String referralsEndpoint = '/social/referrals';
  static const String pickRoomsEndpoint = '/social/pick-rooms';
  static const String recapEndpoint = '/social/recap';
  static const String clubsEndpoint = '/social/clubs';
  static const String challengesEndpoint = '/social/challenges';
  static const String groupMatchmakingEndpoint = '/ai/group-matchmaking';

  // Endpoints — Data Import (Part 3.9): CSV/JSON/plain-text portability.
  static const String importPreviewEndpoint = '/v1/personal/import/preview';
  static const String importApplyEndpoint = '/v1/personal/import/apply';
}
