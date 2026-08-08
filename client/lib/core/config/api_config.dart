// CineVault OS — Client API Configuration Baseline
// Defines server endpoint routes, default timeouts, and client headers

class ApiConfig {
  static const String baseUrl = 'http://localhost:8000';
  
  // Timeout settings
  static const Duration connectTimeout = Duration(seconds: 10);
  static const Duration receiveTimeout = Duration(seconds: 15);
  
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
