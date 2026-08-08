// CineVault OS — Canonical Title Domain Entities (8.1, 8.6)

class AvailabilityEntity {
  final String availabilityId;
  final String platformName;
  final String availabilityType; // FLATRATE, RENT, BUY, FREE
  final double? price;
  final String? currency;
  final String? validFrom;

  const AvailabilityEntity({
    required this.availabilityId,
    required this.platformName,
    required this.availabilityType,
    this.price,
    this.currency,
    this.validFrom,
  });

  factory AvailabilityEntity.fromJson(Map<String, dynamic> json) {
    return AvailabilityEntity(
      availabilityId: json['availability_id'] ?? '',
      platformName: json['platform_name'] ?? json['platform'] ?? 'Unknown Platform',
      availabilityType: json['availability_type'] ?? 'FLATRATE',
      price: json['price'] != null ? (json['price'] as num).toDouble() : null,
      currency: json['currency'],
      validFrom: json['valid_from'],
    );
  }
}

class ReleaseEntity {
  final String releaseId;
  final String platform;
  final String releaseType;
  final String region;
  final String? releaseDate;
  final bool isAvailable;

  const ReleaseEntity({
    required this.releaseId,
    required this.platform,
    required this.releaseType,
    required this.region,
    this.releaseDate,
    required this.isAvailable,
  });

  factory ReleaseEntity.fromJson(Map<String, dynamic> json) {
    return ReleaseEntity(
      releaseId: json['release_id'] ?? '',
      platform: json['platform'] ?? '',
      releaseType: json['release_type'] ?? 'DIGITAL',
      region: json['region'] ?? 'GLOBAL',
      releaseDate: json['release_date'],
      isAvailable: json['is_available'] ?? true,
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
    required this.genres,
    this.availabilities = const [],
    this.releases = const [],
  });

  factory CanonicalTitleEntity.fromJson(Map<String, dynamic> json) {
    return CanonicalTitleEntity(
      titleId: json['title_id'] ?? json['id'] ?? '',
      displayId: json['display_id'] ?? '',
      primaryTitle: json['primary_title'] ?? json['title'] ?? 'Untitled',
      originalTitle: json['original_title'],
      contentType: json['content_type'] ?? 'MOVIE',
      releaseYear: json['release_year'] ?? json['year'],
      runtimeMinutes: json['runtime_minutes'],
      overview: json['overview'] ?? json['description'],
      posterUrl: json['poster_url'],
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
      'primary_title': primaryTitle,
      'original_title': originalTitle,
      'content_type': contentType,
      'release_year': releaseYear,
      'runtime_minutes': runtimeMinutes,
      'overview': overview,
      'poster_url': posterUrl,
      'genres': genres,
    };
  }
}
