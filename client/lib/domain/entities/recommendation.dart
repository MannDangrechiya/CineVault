// CineVault OS — Recommendation Entities (8.7)
// Grounded explanations, transparent score breakdowns, candidate items

class GroundedExplanationEntity {
  final String explanationText;
  final List<String> matchedGenres;
  final List<String> matchedDirectors;
  final List<String> matchedActors;
  final String? seedTitleName;
  final int? userRatingApplied;

  const GroundedExplanationEntity({
    required this.explanationText,
    required this.matchedGenres,
    required this.matchedDirectors,
    required this.matchedActors,
    this.seedTitleName,
    this.userRatingApplied,
  });

  factory GroundedExplanationEntity.fromJson(Map<String, dynamic> json) {
    return GroundedExplanationEntity(
      explanationText: json['explanation_text'] ?? json['textual_explanation'] ?? json['explanation'] ?? 'Recommended based on your taste profile.',
      matchedGenres: json['matched_genres'] != null ? List<String>.from(json['matched_genres']) : [],
      matchedDirectors: json['matched_directors'] != null ? List<String>.from(json['matched_directors']) : [],
      matchedActors: json['matched_actors'] != null ? List<String>.from(json['matched_actors']) : [],
      seedTitleName: json['seed_title_name'],
      userRatingApplied: json['user_rating_applied'],
    );
  }
}

class RecommendationItemEntity {
  final String titleId;
  final String displayId;
  final String titleName;
  final String contentType;
  final int? releaseYear;
  final int? runtimeMinutes;
  final double voteAverage;
  final List<String> genres;
  final List<String> directors;
  final double recommendationScore;
  final bool isAvailable;
  final GroundedExplanationEntity groundedExplanation;

  const RecommendationItemEntity({
    required this.titleId,
    required this.displayId,
    required this.titleName,
    required this.contentType,
    this.releaseYear,
    this.runtimeMinutes,
    this.voteAverage = 0.0,
    required this.genres,
    required this.directors,
    required this.recommendationScore,
    this.isAvailable = true,
    required this.groundedExplanation,
  });

  factory RecommendationItemEntity.fromJson(Map<String, dynamic> json) {
    final explanationData = json['explanation'] ?? json['grounded_explanation'];
    final explanation = explanationData is Map<String, dynamic>
        ? GroundedExplanationEntity.fromJson(explanationData)
        : GroundedExplanationEntity(
            explanationText: explanationData?.toString() ?? 'Recommended item.',
            matchedGenres: const [],
            matchedDirectors: const [],
            matchedActors: const [],
          );

    return RecommendationItemEntity(
      titleId: json['title_id'] ?? json['id'] ?? '',
      displayId: json['display_id'] ?? '',
      // Backend uses canonical_title in RecommendationItemResponse
      titleName: json['canonical_title'] ?? json['title_name'] ?? json['title'] ?? 'Untitled',
      contentType: json['content_type'] ?? 'MOVIE',
      releaseYear: json['release_year'] ?? json['year'],
      runtimeMinutes: json['runtime_minutes'],
      voteAverage: (json['vote_average'] as num?)?.toDouble() ?? 0.0,
      genres: json['genres'] != null ? List<String>.from(json['genres']) : [],
      directors: json['directors'] != null ? List<String>.from(json['directors']) : [],
      recommendationScore: (json['recommendation_score'] ?? json['score'] as num?)?.toDouble() ?? 0.0,
      isAvailable: json['is_available'] ?? true,
      groundedExplanation: explanation,
    );
  }
}
