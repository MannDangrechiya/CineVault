// CineVault OS — Canonical Title Domain Entities (8.1, 8.6)

class AvailabilityEntity {
  final String offerId;
  final String platformName;
  final String offerType; // FLATRATE, RENT, BUY, FREE, ADS
  final String? platformCode;
  final String? countryCode;
  final String? validFrom;
  final String? validTo;

  const AvailabilityEntity({
    required this.offerId,
    required this.platformName,
    required this.offerType,
    this.platformCode,
    this.countryCode,
    this.validFrom,
    this.validTo,
  });

  factory AvailabilityEntity.fromJson(Map<String, dynamic> json) {
    return AvailabilityEntity(
      offerId: json['offer_id'] ?? json['availability_id'] ?? '',
      platformName: json['platform_name'] ?? json['platform'] ?? 'Unknown Platform',
      offerType: json['offer_type'] ?? json['availability_type'] ?? 'FLATRATE',
      platformCode: json['platform_code'],
      countryCode: json['country_code'],
      validFrom: json['valid_from'],
      validTo: json['valid_to'],
    );
  }
}

class ReleaseEntity {
  final String releaseId;
  final String editionId;
  final String releaseName;
  final String releaseType;
  final String? countryCode;
  final String? releaseDate;

  const ReleaseEntity({
    required this.releaseId,
    required this.editionId,
    required this.releaseName,
    required this.releaseType,
    this.countryCode,
    this.releaseDate,
  });

  factory ReleaseEntity.fromJson(Map<String, dynamic> json) {
    return ReleaseEntity(
      releaseId: json['release_id'] ?? '',
      editionId: json['edition_id'] ?? '',
      releaseName: json['release_name'] ?? '',
      releaseType: json['release_type'] ?? 'DIGITAL',
      countryCode: json['country_code'] ?? json['region'],
      releaseDate: json['release_date'],
    );
  }
}

class CanonicalTitleEntity {
  final String titleId;
  final String displayId;
  final String primaryTitle;
  final String? originalTitle;
  final String contentType;
  final int? releaseYear;
  final int? runtimeMinutes;
  final String? overview;
  final String? posterUrl;
  final String? backdropUrl;
  final List<String> genres;
  final List<AvailabilityEntity> availabilities;
  final List<ReleaseEntity> releases;

  const CanonicalTitleEntity({
    required this.titleId,
    required this.displayId,
    required this.primaryTitle,
    this.originalTitle,
    required this.contentType,
    this.releaseYear,
    this.runtimeMinutes,
    this.overview,
    this.posterUrl,
    this.backdropUrl,
    required this.genres,
    this.availabilities = const [],
    this.releases = const [],
  });

  factory CanonicalTitleEntity.fromJson(Map<String, dynamic> json) {
    // Extract runtime from nested primary_edition if present (TitleDetail schema)
    int? runtime = json['runtime_minutes'];
    if (runtime == null && json['primary_edition'] is Map<String, dynamic>) {
      runtime = json['primary_edition']['runtime_minutes'];
    }

    return CanonicalTitleEntity(
      titleId: json['title_id'] ?? json['id'] ?? '',
      displayId: json['display_id'] ?? '',
      // Backend uses canonical_title; fallback to primary_title/title for compatibility
      primaryTitle: json['canonical_title'] ?? json['primary_title'] ?? json['title'] ?? 'Untitled',
      originalTitle: json['original_title'],
      contentType: json['content_type'] ?? 'MOVIE',
      // Backend uses production_year; fallback to release_year/year for recommendation responses
      releaseYear: json['production_year'] ?? json['release_year'] ?? json['year'],
      runtimeMinutes: runtime,
      // Backend TitleDetail uses synopsis; fallback for other contexts
      overview: json['synopsis'] ?? json['overview'] ?? json['description'],
      posterUrl: json['poster_url'],
      backdropUrl: json['backdrop_url'],
      genres: json['genres'] != null ? List<String>.from(json['genres']) : [],
      availabilities: json['availabilities'] != null
          ? (json['availabilities'] as List)
              .map((e) => AvailabilityEntity.fromJson(e))
              .toList()
          : [],
      releases: json['releases'] != null
          ? (json['releases'] as List)
              .map((e) => ReleaseEntity.fromJson(e))
              .toList()
          : [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'title_id': titleId,
      'display_id': displayId,
      'canonical_title': primaryTitle,
      'original_title': originalTitle,
      'content_type': contentType,
      'production_year': releaseYear,
      'runtime_minutes': runtimeMinutes,
      'synopsis': overview,
      'poster_url': posterUrl,
      'backdrop_url': backdropUrl,
      'genres': genres,
    };
  }
}
