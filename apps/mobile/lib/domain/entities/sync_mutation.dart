// CineVault OS — Sync Outbox Mutation Entity (8.9 / ADR-004)
// Client-side mutation representation for durable offline queue

class SyncMutationEntity {
  final String mutationId; // Client-generated UUIDv7
  final String mutationType; // CREATE_WATCH_EVENT, SET_RATING, UPSERT_NOTE
  final String clientTimestamp; // ISO-8601 UTC
  final Map<String, dynamic> payload;
  final String status; // PENDING, SYNCED, FAILED

  const SyncMutationEntity({
    required this.mutationId,
    required this.mutationType,
    required this.clientTimestamp,
    required this.payload,
    this.status = 'PENDING',
  });

  factory SyncMutationEntity.fromJson(Map<String, dynamic> json) {
    return SyncMutationEntity(
      mutationId: json['mutation_id'] ?? '',
      mutationType: json['mutation_type'] ?? '',
      clientTimestamp: json['client_timestamp'] ?? DateTime.now().toIso8601String(),
      payload: json['payload'] != null ? Map<String, dynamic>.from(json['payload']) : {},
      status: json['status'] ?? 'PENDING',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'mutation_id': mutationId,
      'mutation_type': mutationType,
      'client_timestamp': clientTimestamp,
      'payload': payload,
    };
  }
}

class SyncPushResultEntity {
  final int processedCount;
  final List<String> acknowledgedMutationIds;
  final List<Map<String, dynamic>> failedMutations;

  const SyncPushResultEntity({
    required this.processedCount,
    required this.acknowledgedMutationIds,
    required this.failedMutations,
  });

  factory SyncPushResultEntity.fromJson(Map<String, dynamic> json) {
    return SyncPushResultEntity(
      processedCount: json['processed_count'] ?? 0,
      acknowledgedMutationIds: json['acknowledged_mutation_ids'] != null
          ? List<String>.from(json['acknowledged_mutation_ids'])
          : [],
      failedMutations: json['failed_mutations'] != null
          ? List<Map<String, dynamic>>.from(json['failed_mutations'])
          : [],
    );
  }
}
