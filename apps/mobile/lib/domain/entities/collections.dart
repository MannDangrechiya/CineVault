// CineVault OS — Collections Domain Entities (Part 3.5)
// User-curated title lists. Mirrors apps/web/src/lib/api/collections.ts.

class CollectionEntity {
  final String id;
  final String name;
  final String? description;
  final int itemCount;
  final String? bannerUrl;
  final List<String> tags;
  final bool isPrivate;
  final String? createdAt;

  const CollectionEntity({
    required this.id,
    required this.name,
    this.description,
    this.itemCount = 0,
    this.bannerUrl,
    this.tags = const [],
    this.isPrivate = false,
    this.createdAt,
  });

  factory CollectionEntity.fromJson(Map<String, dynamic> json) {
    return CollectionEntity(
      id: json['id'] ?? '',
      name: json['name'] ?? '',
      description: json['description'],
      itemCount: (json['item_count'] as num?)?.toInt() ?? 0,
      bannerUrl: json['banner_url'],
      tags: List<String>.from(json['tags'] ?? const []),
      isPrivate: json['is_private'] ?? false,
      createdAt: json['created_at'],
    );
  }
}

class CollectionTitleItemEntity {
  final String itemId;
  final String titleId;
  final String canonicalTitle;
  final int? productionYear;
  final String contentType;
  final String? posterUrl;
  final String? notes;
  final String addedAt;

  const CollectionTitleItemEntity({
    required this.itemId,
    required this.titleId,
    required this.canonicalTitle,
    this.productionYear,
    required this.contentType,
    this.posterUrl,
    this.notes,
    required this.addedAt,
  });

  factory CollectionTitleItemEntity.fromJson(Map<String, dynamic> json) {
    return CollectionTitleItemEntity(
      itemId: json['item_id'] ?? '',
      titleId: json['title_id'] ?? '',
      canonicalTitle: json['canonical_title'] ?? '',
      productionYear: (json['production_year'] as num?)?.toInt(),
      contentType: json['content_type'] ?? '',
      posterUrl: json['poster_url'],
      notes: json['notes'],
      addedAt: json['added_at'] ?? DateTime.now().toIso8601String(),
    );
  }
}

class CollectionDetailEntity {
  final CollectionEntity collection;
  final List<CollectionTitleItemEntity> items;

  const CollectionDetailEntity({required this.collection, required this.items});

  factory CollectionDetailEntity.fromJson(Map<String, dynamic> json) {
    return CollectionDetailEntity(
      collection: CollectionEntity.fromJson(json['collection'] as Map<String, dynamic>),
      items: (json['items'] as List? ?? const [])
          .map((e) => CollectionTitleItemEntity.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}
