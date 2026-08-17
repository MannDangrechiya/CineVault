// CineVault OS — Phase 18: Offline Personal Library Unit Tests
// Validates offline personal data persistence, outbox mutation queueing, and non-authoritative cache constraints

import 'package:flutter_test/flutter_test.dart';
import 'package:drift/native.dart';
import 'package:cinevault_client/data/local/app_database.dart';
import 'package:cinevault_client/data/repositories/personal_offline_repository.dart';

void main() {
  late AppDatabase db;
  late PersonalOfflineRepository repository;

  setUp(() {
    db = AppDatabase(NativeDatabase.memory());
    repository = PersonalOfflineRepository(db);
  });

  tearDown(() async {
    await db.close();
  });

  group('Phase 18 — Offline Personal Library & Cache Tests', () {
    test('Offline watch event recording writes to local table and queues outbox mutation', () async {
      const titleId = '018f4a00-0000-7000-8000-000000000001';
      final event = await repository.recordOfflineWatchEvent(
        titleId: titleId,
        notes: 'Watched offline on plane',
        progressPercentage: 100.0,
      );

      expect(event.titleId, equals(titleId));
      expect(event.progressPercentage, equals(100.0));

      // Verify local offline table read
      final history = await repository.getOfflineWatchHistory();
      expect(history.length, equals(1));
      expect(history.first.titleId, equals(titleId));

      // Verify mutation queued into Outbox
      final pendingMutations = await db.getPendingMutations();
      expect(pendingMutations.length, equals(1));
      expect(pendingMutations.first.mutationType, equals('CREATE_WATCH_EVENT'));
    });

    test('Offline rating upsert writes to local table and queues outbox mutation', () async {
      const titleId = '018f4a00-0000-7000-8000-000000000002';
      final rating = await repository.setOfflineRating(
        titleId: titleId,
        ratingValue: 9,
      );

      expect(rating.titleId, equals(titleId));
      expect(rating.ratingValue, equals(9));

      final ratings = await repository.getOfflineRatings();
      expect(ratings.length, equals(1));
      expect(ratings.first.ratingValue, equals(9));

      final forTitle = await repository.getOfflineRatingForTitle(titleId);
      expect(forTitle, isNotNull);
      expect(forTitle!.ratingValue, equals(9));

      final pending = await db.getPendingMutations();
      expect(pending.any((m) => m.mutationType == 'SET_RATING'), isTrue);
    });

    test('Offline title state update persists favorites and queues outbox mutation', () async {
      const titleId = '018f4a00-0000-7000-8000-000000000003';
      final state = await repository.updateOfflineTitleState(
        titleId: titleId,
        manualStatusOverride: 'COMPLETED',
        isFavorite: true,
      );

      expect(state.titleId, equals(titleId));
      expect(state.manualStatusOverride, equals('COMPLETED'));
      expect(state.isFavorite, isTrue);

      final favorites = await repository.getOfflineFavorites();
      expect(favorites.length, equals(1));
      expect(favorites.first.titleId, equals(titleId));

      final pending = await db.getPendingMutations();
      expect(pending.any((m) => m.mutationType == 'UPDATE_TITLE_STATE'), isTrue);
    });

    test('Offline personal notes write to local table and queue outbox mutation', () async {
      const titleId = '018f4a00-0000-7000-8000-000000000004';
      final note = await repository.addOfflineNote(
        titleId: titleId,
        noteText: 'Exceptional screenplay and pacing',
      );

      expect(note.titleId, equals(titleId));
      expect(note.noteText, equals('Exceptional screenplay and pacing'));

      final notes = await repository.getOfflineNotes();
      expect(notes.length, equals(1));
      expect(notes.first.noteText, equals('Exceptional screenplay and pacing'));

      final pending = await db.getPendingMutations();
      expect(pending.any((m) => m.mutationType == 'CREATE_NOTE'), isTrue);
    });

    test('Constraint: Cached canonical metadata is strictly non-authoritative', () async {
      const titleId = '018f4a00-0000-7000-8000-000000000005';
      await repository.cacheCanonicalTitle(
        titleId: titleId,
        displayId: 'MOV-OFF-001',
        primaryTitle: 'Inception',
        contentType: 'movie',
        releaseYear: 2010,
        genres: ['Sci-Fi', 'Action'],
      );

      final cached = await repository.getCachedTitle(titleId);
      expect(cached, isNotNull);
      expect(cached!.primaryTitle, equals('Inception'));
      expect(cached.releaseYear, equals(2010));
      // Constraint check: offline metadata MUST NOT be treated as authoritative canonical data
      expect(cached.isAuthoritative, isFalse);
    });
  });
}
