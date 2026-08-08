// CineVault OS — Offline Sync Outbox Mutation Unit Tests (ADR-004)

import 'package:flutter_test/flutter_test.dart';
import 'package:cinevault_client/core/utils/uuid_util.dart';
import 'package:cinevault_client/domain/entities/sync_mutation.dart';

void main() {
  group('Sync Outbox Mutation Tests (ADR-004)', () {
    test('Generates valid UUIDv7 mutation ID', () {
      final mutationId1 = UuidUtil.generateMutationId();
      final mutationId2 = UuidUtil.generateMutationId();

      expect(mutationId1, isNotEmpty);
      expect(mutationId2, isNotEmpty);
      expect(mutationId1, isNot(equals(mutationId2)));
    });

    test('SyncMutationEntity serializes to JSON for POST /v1/sync/push', () {
      final mutationId = UuidUtil.generateMutationId();
      final timestamp = DateTime.now().toUtc().toIso8601String();

      final mutation = SyncMutationEntity(
        mutationId: mutationId,
        mutationType: 'CREATE_WATCH_EVENT',
        clientTimestamp: timestamp,
        payload: {
          'title_id': '01912345-6789-7000-8000-000000000001',
          'watch_mode': 'STREAMING',
          'rating_value': 9.0,
        },
      );

      final json = mutation.toJson();

      expect(json['mutation_id'], equals(mutationId));
      expect(json['mutation_type'], equals('CREATE_WATCH_EVENT'));
      expect(json['client_timestamp'], equals(timestamp));
      expect(json['payload']['title_id'], equals('01912345-6789-7000-8000-000000000001'));
      expect(json['payload']['rating_value'], equals(9.0));
    });

    test('SyncPushResultEntity parses server push response correctly', () {
      final mutationId1 = UuidUtil.generateMutationId();
      final mutationId2 = UuidUtil.generateMutationId();

      final json = {
        'processed_count': 2,
        'acknowledged_mutation_ids': [mutationId1, mutationId2],
        'failed_mutations': [],
      };

      final result = SyncPushResultEntity.fromJson(json);

      expect(result.processedCount, equals(2));
      expect(result.acknowledgedMutationIds, contains(mutationId1));
      expect(result.acknowledgedMutationIds, contains(mutationId2));
      expect(result.failedMutations, isEmpty);
    });
  });
}
