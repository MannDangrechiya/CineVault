// CineVault OS — AI Assistant Entities (8.8)
// Grounded assistant responses & intent extraction models

class AiIntentEntity {
  final String intentType; // SEARCH, RECOMMENDATION, GENERAL_QUERY
  final String? primaryKeyword;
  final Map<String, dynamic> extractedFilters;

  const AiIntentEntity({
    required this.intentType,
    this.primaryKeyword,
    required this.extractedFilters,
  });

  factory AiIntentEntity.fromJson(Map<String, dynamic> json) {
    return AiIntentEntity(
      intentType: json['intent_type'] ?? 'SEARCH',
      primaryKeyword: json['primary_keyword'],
      extractedFilters: json['extracted_filters'] != null ? Map<String, dynamic>.from(json['extracted_filters']) : {},
    );
  }
}

class AiResponseEntity {
  final String queryId;
  final String rawQuery;
  final String responseText;
  final AiIntentEntity detectedIntent;
  final List<String> titleCitations;
  final double confidenceScore;

  const AiResponseEntity({
    required this.queryId,
    required this.rawQuery,
    required this.responseText,
    required this.detectedIntent,
    required this.titleCitations,
    required this.confidenceScore,
  });

  factory AiResponseEntity.fromJson(Map<String, dynamic> json) {
    return AiResponseEntity(
      queryId: json['query_id'] ?? '',
      rawQuery: json['raw_query'] ?? '',
      responseText: json['response_text'] ?? '',
      detectedIntent: json['detected_intent'] != null
          ? AiIntentEntity.fromJson(json['detected_intent'])
          : const AiIntentEntity(intentType: 'GENERAL_QUERY', extractedFilters: {}),
      titleCitations: json['title_citations'] != null ? List<String>.from(json['title_citations']) : [],
      confidenceScore: (json['confidence_score'] as num?)?.toDouble() ?? 0.9,
    );
  }
}
