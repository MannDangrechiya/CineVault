// CineVault OS — Sync Repository Implementation (8.9 / ADR-004)
// Manages local outbox mutation queueing, push execution, idempotency, and delta pulling

import 'dart:convert';
import 'package:drift/drift.dart';
import '../../core/utils/uuid_util.dart';
import '../../domain/entities/sync_mutation.dart';
import '../local/app_database.dart';
import '../remote/sync_remote_datasource.dart';

class SyncRepositoryImpl {
  final AppDatabase _db;
  final SyncRemoteDatasource _remoteDatasource;

  SyncRepositoryImpl(this._db, this._remoteDatasource);

  /// Queue a mutation into the durable local outbox table with client UUIDv7 mutation_id
  Future<SyncMutationEntity> queueMutation({
    required String mutationType,
    required Map<String, dynamic> payload,
  }) async {
    final mutationId = UuidUtil.generateMutationId();
    final clientTimestamp = DateTime.now().toUtc().toIso8601String();

    await _db.insertMutation(
      OutboxMutationsCompanion.insert(
        mutationId: mutationId,
        mutationType: mutationType,
        clientTimestamp: clientTimestamp,
        payloadJson: jsonEncode(payload),
        status: const Value('PENDING'),
      ),
    );

    return SyncMutationEntity(
      mutationId: mutationId,
      mutationType: mutationType,
      clientTimestamp: clientTimestamp,
      payload: payload,
      status: 'PENDING',
    );
  }

  /// Retrieves pending local outbox mutations
  Future<List<SyncMutationEntity>> getPendingMutations() async {
    final rows = await _db.getPendingMutations();
    return rows.map((row) {
      return SyncMutationEntity(
        mutationId: row.mutationId,
        mutationType: row.mutationType,
        clientTimestamp: row.clientTimestamp,
        payload: jsonDecode(row.payloadJson),
        status: row.status,
      );
    }).toList();
  }

  /// Pushes pending outbox batch to server POST /v1/sync/push and marks acknowledged items synced
  Future<SyncPushResultEntity> processOutboxSync() async {
    final pending = await getPendingMutations();
    if (pending.isEmpty) {
      return const SyncPushResultEntity(
        processedCount: 0,
        acknowledgedMutationIds: [],
        failedMutations: [],
      );
    }

    final result = await _remoteDatasource.pushMutations(pending);

    if (result.acknowledgedMutationIds.isNotEmpty) {
      await _db.markMutationsSynced(result.acknowledgedMutationIds);
    }

    return result;
  }
}
