// CineVault OS — AI Assistant Entities (8.8)
// Grounded assistant responses & intent extraction models

class AiIntentEntity {
  final String detectedIntentMode; // SEARCH, RECOMMENDATION, SIMILARITY, GENERAL_SEARCH
  final String? sanitizedQuery;
  final String? rawQuery;
  final List<String> targetGenres;
  final List<String> targetDirectors;
  final List<String> targetActors;
  final int? minYear;
  final int? maxYear;
  final int? maxRuntime;
  final String? preferredContentType;

  const AiIntentEntity({
    required this.detectedIntentMode,
    this.sanitizedQuery,
    this.rawQuery,
    this.targetGenres = const [],
    this.targetDirectors = const [],
    this.targetActors = const [],
    this.minYear,
    this.maxYear,
    this.maxRuntime,
    this.preferredContentType,
  });

  factory AiIntentEntity.fromJson(Map<String, dynamic> json) {
    return AiIntentEntity(
      detectedIntentMode: json['detected_intent_mode'] ?? json['intent_type'] ?? 'GENERAL_SEARCH',
      sanitizedQuery: json['sanitized_query'] ?? json['primary_keyword'],
      rawQuery: json['raw_query'],
      targetGenres: json['target_genres'] != null ? List<String>.from(json['target_genres']) : [],
      targetDirectors: json['target_directors'] != null ? List<String>.from(json['target_directors']) : [],
      targetActors: json['target_actors'] != null ? List<String>.from(json['target_actors']) : [],
      minYear: json['min_year'],
      maxYear: json['max_year'],
      maxRuntime: json['max_runtime'],
      preferredContentType: json['preferred_content_type'],
    );
  }
}

class AiResponseEntity {
  final String responseText;
  final AiIntentEntity intent;
  final List<Map<String, dynamic>> matchedTitles;
  final String providerUsed;
  final bool isGrounded;
  final bool fallbackApplied;

  const AiResponseEntity({
    required this.responseText,
    required this.intent,
    required this.matchedTitles,
    required this.providerUsed,
    this.isGrounded = true,
    this.fallbackApplied = false,
  });

  factory AiResponseEntity.fromJson(Map<String, dynamic> json) {
    // Backend returns 'intent' not 'detected_intent'
    final intentData = json['intent'] ?? json['detected_intent'];
    final intent = intentData is Map<String, dynamic>
        ? AiIntentEntity.fromJson(intentData)
        : const AiIntentEntity(detectedIntentMode: 'GENERAL_SEARCH');

    // Backend returns 'matched_titles' not 'title_citations'
    final matchedTitlesRaw = json['matched_titles'] ?? json['title_citations'] ?? [];
    final List<Map<String, dynamic>> matchedTitles = matchedTitlesRaw is List
        ? matchedTitlesRaw.map<Map<String, dynamic>>((e) {
            if (e is Map<String, dynamic>) return e;
            if (e is String) return {'title': e};
            return <String, dynamic>{};
          }).toList()
        : [];

    return AiResponseEntity(
      responseText: json['response_text'] ?? '',
      intent: intent,
      matchedTitles: matchedTitles,
      providerUsed: json['provider_used'] ?? 'mock',
      isGrounded: json['is_grounded'] ?? true,
      fallbackApplied: json['fallback_applied'] ?? false,
    );
  }
}
