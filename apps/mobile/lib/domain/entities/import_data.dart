// CineVault OS — Data Import Domain Entities (Part 3.9)
// Mirrors apps/web/src/lib/api/import.ts's CSV/JSON/plain-text import
// pipeline. Named import_data.dart (not import.dart) since `import` is a
// Dart reserved word and can't lead a file/library name.

class ImportItem {
  final String canonicalTitle;
  final int? productionYear;
  final String? titleId;
  final String? watchedAt;
  final double? progressPercentage;
  final int? ratingValue;
  final bool isFavorite;
  final String? manualStatusOverride;
  final String? notes;

  const ImportItem({
    required this.canonicalTitle,
    this.productionYear,
    this.titleId,
    this.watchedAt,
    this.progressPercentage,
    this.ratingValue,
    this.isFavorite = false,
    this.manualStatusOverride,
    this.notes,
  });

  Map<String, dynamic> toJson() {
    return {
      'canonical_title': canonicalTitle,
      if (productionYear != null) 'production_year': productionYear,
      if (titleId != null) 'title_id': titleId,
      if (watchedAt != null) 'watched_at': watchedAt,
      if (progressPercentage != null) 'progress_percentage': progressPercentage,
      if (ratingValue != null) 'rating_value': ratingValue,
      'is_favorite': isFavorite,
      if (manualStatusOverride != null) 'manual_status_override': manualStatusOverride,
      if (notes != null) 'notes': notes,
    };
  }
}

/// One row's match verdict, per PLAN.md 3.9's "per-item confidence badges
/// (Exact/Probable/Unmatched)". A 4th tier (REVIEW_REQUIRED) exists on the
/// backend between probable and unmatched.
enum ImportVerdict { exactMatch, probableMatch, reviewRequired, unmatched }

ImportVerdict _verdictFromJson(String? raw) {
  switch (raw) {
    case 'EXACT_MATCH':
      return ImportVerdict.exactMatch;
    case 'PROBABLE_MATCH':
      return ImportVerdict.probableMatch;
    case 'REVIEW_REQUIRED':
      return ImportVerdict.reviewRequired;
    default:
      return ImportVerdict.unmatched;
  }
}

class ImportCandidateMatch {
  final String titleId;
  final String canonicalTitle;
  final int? productionYear;
  final double confidence;

  const ImportCandidateMatch({
    required this.titleId,
    required this.canonicalTitle,
    this.productionYear,
    required this.confidence,
  });

  factory ImportCandidateMatch.fromJson(Map<String, dynamic> json) {
    return ImportCandidateMatch(
      titleId: json['title_id'] ?? '',
      canonicalTitle: json['canonical_title'] ?? '',
      productionYear: (json['production_year'] as num?)?.toInt(),
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class ImportItemVerdictResult {
  final int index;
  final String canonicalTitle;
  final int? productionYear;
  final bool matched;
  final String? matchedTitleId;
  final double confidenceScore;
  final ImportVerdict verdict;
  final List<ImportCandidateMatch> candidates;

  const ImportItemVerdictResult({
    required this.index,
    required this.canonicalTitle,
    this.productionYear,
    this.matched = false,
    this.matchedTitleId,
    this.confidenceScore = 0.0,
    required this.verdict,
    this.candidates = const [],
  });

  factory ImportItemVerdictResult.fromJson(Map<String, dynamic> json) {
    return ImportItemVerdictResult(
      index: (json['index'] as num?)?.toInt() ?? 0,
      canonicalTitle: json['canonical_title'] ?? '',
      productionYear: (json['production_year'] as num?)?.toInt(),
      matched: json['matched'] ?? false,
      matchedTitleId: json['matched_title_id'],
      confidenceScore: (json['confidence_score'] as num?)?.toDouble() ?? 0.0,
      verdict: _verdictFromJson(json['verdict']),
      candidates: (json['candidates'] as List? ?? const [])
          .map((e) => ImportCandidateMatch.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

class ImportPreviewResult {
  final int totalItems;
  final int matchedTitles;
  final int probableMatches;
  final int reviewRequired;
  final int unmatchedTitles;
  final int conflictsCount;
  final List<ImportItemVerdictResult> itemVerdicts;

  const ImportPreviewResult({
    this.totalItems = 0,
    this.matchedTitles = 0,
    this.probableMatches = 0,
    this.reviewRequired = 0,
    this.unmatchedTitles = 0,
    this.conflictsCount = 0,
    this.itemVerdicts = const [],
  });

  factory ImportPreviewResult.fromJson(Map<String, dynamic> json) {
    return ImportPreviewResult(
      totalItems: (json['total_items'] as num?)?.toInt() ?? 0,
      matchedTitles: (json['matched_titles'] as num?)?.toInt() ?? 0,
      probableMatches: (json['probable_matches'] as num?)?.toInt() ?? 0,
      reviewRequired: (json['review_required'] as num?)?.toInt() ?? 0,
      unmatchedTitles: (json['unmatched_titles'] as num?)?.toInt() ?? 0,
      conflictsCount: (json['conflicts_count'] as num?)?.toInt() ?? 0,
      itemVerdicts: (json['item_verdicts'] as List? ?? const [])
          .map((e) => ImportItemVerdictResult.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

class ImportApplyResult {
  final int appliedCount;
  final int conflictsResolved;
  final String strategyApplied;

  const ImportApplyResult({
    this.appliedCount = 0,
    this.conflictsResolved = 0,
    this.strategyApplied = 'KEEP_EXISTING',
  });

  factory ImportApplyResult.fromJson(Map<String, dynamic> json) {
    return ImportApplyResult(
      appliedCount: (json['applied_count'] as num?)?.toInt() ?? 0,
      conflictsResolved: (json['conflicts_resolved'] as num?)?.toInt() ?? 0,
      strategyApplied: json['strategy_applied'] ?? 'KEEP_EXISTING',
    );
  }
}
