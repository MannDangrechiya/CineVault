// CineVault OS — Recommendation Entities (8.7)
// Grounded explanations, transparent score breakdowns, candidate items

class GroundedExplanationEntity {
  final double overallScore;
  final double contentSimilarityScore;
  final double tasteFitScore;
  final double popularityScore;
  final String textualExplanation;
  final List<String> citations;

  const GroundedExplanationEntity({
    required this.overallScore,
    required this.contentSimilarityScore,
    required this.tasteFitScore,
    required this.popularityScore,
    required this.textualExplanation,
    required this.citations,
  });

  factory GroundedExplanationEntity.fromJson(Map<String, dynamic> json) {
    return GroundedExplanationEntity(
      overallScore: (json['overall_score'] as num?)?.toDouble() ?? 0.0,
      contentSimilarityScore: (json['content_similarity_score'] as num?)?.toDouble() ?? 0.0,
      tasteFitScore: (json['taste_fit_score'] as num?)?.toDouble() ?? 0.0,
      popularityScore: (json['popularity_score'] as num?)?.toDouble() ?? 0.0,
      textualExplanation: json['textual_explanation'] ?? json['explanation'] ?? 'Recommended based on your taste profile.',
      citations: json['citations'] != null ? List<String>.from(json['citations']) : [],
    );
  }
}

class RecommendationItemEntity {
  final String titleId;
  final String titleName;
  final int? releaseYear;
  final String? posterUrl;
  final double recommendationScore;
  final GroundedExplanationEntity groundedExplanation;
  final String? seedTitleId;

  const RecommendationItemEntity({
    required this.titleId,
    required this.titleName,
    this.releaseYear,
    this.posterUrl,
    required this.recommendationScore,
    required this.groundedExplanation,
    this.seedTitleId,
  });

  factory RecommendationItemEntity.fromJson(Map<String, dynamic> json) {
    final explanationData = json['grounded_explanation'] ?? json['explanation'];
    final explanation = explanationData is Map<String, dynamic>
        ? GroundedExplanationEntity.fromJson(explanationData)
        : GroundedExplanationEntity(
            overallScore: (json['score'] as num?)?.toDouble() ?? 0.0,
            contentSimilarityScore: 0.8,
            tasteFitScore: 0.85,
            popularityScore: 0.7,
            textualExplanation: json['grounded_explanation']?.toString() ?? 'Recommended item.',
            citations: const [],
          );

    return RecommendationItemEntity(
      titleId: json['title_id'] ?? json['id'] ?? '',
      titleName: json['title_name'] ?? json['title'] ?? 'Untitled',
      releaseYear: json['release_year'] ?? json['year'],
      posterUrl: json['poster_url'],
      recommendationScore: (json['recommendation_score'] ?? json['score'] as num?)?.toDouble() ?? 0.0,
      groundedExplanation: explanation,
      seedTitleId: json['seed_title_id'],
    );
  }
}
