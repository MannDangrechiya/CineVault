// CineVault OS — Drift Local Database (8.9, ADR-004, Phase 18 Offline Personal Library)
// Stores durable outbox mutations, local cached canonical metadata, and personal offline records

import 'dart:io';
import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as p;

part 'app_database.g.dart';

// ------------------------------------------------------------------------
// Table Definitions
// ------------------------------------------------------------------------

@DataClassName('OutboxMutationRow')
class OutboxMutations extends Table {
  TextColumn get mutationId => text()(); // Client UUIDv7
  TextColumn get mutationType => text()(); // CREATE_WATCH_EVENT, SET_RATING, UPSERT_NOTE, UPDATE_TITLE_STATE
  TextColumn get clientTimestamp => text()(); // ISO-8601 UTC
  TextColumn get payloadJson => text()(); // Serialized JSON map
  TextColumn get status => text().withDefault(const Constant('PENDING'))(); // PENDING, SYNCED, FAILED
  IntColumn get retryCount => integer().withDefault(const Constant(0))();

  @override
  Set<Column> get primaryKey => {mutationId};
}

@DataClassName('CachedTitleRow')
class CachedTitles extends Table {
  TextColumn get titleId => text()();
  TextColumn get displayId => text()();
  TextColumn get primaryTitle => text()();
  TextColumn get contentType => text()();
  IntColumn get releaseYear => integer().nullable()();
  TextColumn get posterUrl => text().nullable()();
  TextColumn get genresJson => text()();
  TextColumn get cachedAt => text()();
  BoolColumn get isAuthoritative => boolean().withDefault(const Constant(false))(); // Non-authoritative offline cache constraint

  @override
  Set<Column> get primaryKey => {titleId};
}

@DataClassName('OfflineWatchEventRow')
class OfflineWatchEvents extends Table {
  TextColumn get watchEventId => text()();
  TextColumn get titleId => text()();
  TextColumn get watchedAt => text()();
  RealColumn get progressPercentage => real().withDefault(const Constant(100.0))();
  TextColumn get notes => text().nullable()();
  BoolColumn get isTombstoned => boolean().withDefault(const Constant(false))();

  @override
  Set<Column> get primaryKey => {watchEventId};
}

@DataClassName('OfflineRatingRow')
class OfflineRatings extends Table {
  TextColumn get ratingId => text()();
  TextColumn get titleId => text()();
  IntColumn get ratingValue => integer()();
  TextColumn get ratedAt => text()();

  @override
  Set<Column> get primaryKey => {ratingId};
}

@DataClassName('OfflineUserTitleStateRow')
class OfflineUserTitleStates extends Table {
  TextColumn get titleId => text()();
  TextColumn get manualStatusOverride => text().nullable()();
  BoolColumn get isFavorite => boolean().withDefault(const Constant(false))();
  TextColumn get updatedAt => text()();

  @override
  Set<Column> get primaryKey => {titleId};
}

@DataClassName('OfflineNoteRow')
class OfflineNotes extends Table {
  TextColumn get noteId => text()();
  TextColumn get titleId => text()();
  TextColumn get noteText => text()();
  TextColumn get updatedAt => text()();

  @override
  Set<Column> get primaryKey => {noteId};
}

// ------------------------------------------------------------------------
// App Database Class
// ------------------------------------------------------------------------

@DriftDatabase(tables: [
  OutboxMutations,
  CachedTitles,
  OfflineWatchEvents,
  OfflineRatings,
  OfflineUserTitleStates,
  OfflineNotes,
])
class AppDatabase extends _$AppDatabase {
  AppDatabase([QueryExecutor? executor]) : super(executor ?? _openConnection());

  @override
  int get schemaVersion => 1;

  // --- Outbox Mutation Queries ---
  Future<void> insertMutation(OutboxMutationsCompanion mutation) async {
    await into(outboxMutations).insertOnConflictUpdate(mutation);
  }

  Future<List<OutboxMutationRow>> getPendingMutations() async {
    return await (select(outboxMutations)..where((tbl) => tbl.status.equals('PENDING'))).get();
  }

  Future<void> markMutationsSynced(List<String> mutationIds) async {
    await (update(outboxMutations)..where((tbl) => tbl.mutationId.isIn(mutationIds)))
        .write(const OutboxMutationsCompanion(status: Value('SYNCED')));
  }

  Future<void> deleteMutation(String mutationId) async {
    await (delete(outboxMutations)..where((tbl) => tbl.mutationId.equals(mutationId))).go();
  }

  // --- Cached Titles Queries ---
  Future<void> cacheTitle(CachedTitlesCompanion title) async {
    await into(cachedTitles).insertOnConflictUpdate(title);
  }

  Future<List<CachedTitleRow>> getCachedTitles() async {
    return await select(cachedTitles).get();
  }

  Future<CachedTitleRow?> getCachedTitleById(String titleId) async {
    return await (select(cachedTitles)..where((tbl) => tbl.titleId.equals(titleId))).getSingleOrNull();
  }

  // --- Offline Watch Events ---
  Future<void> upsertOfflineWatchEvent(OfflineWatchEventsCompanion event) async {
    await into(offlineWatchEvents).insertOnConflictUpdate(event);
  }

  Future<List<OfflineWatchEventRow>> getOfflineWatchEvents() async {
    return await (select(offlineWatchEvents)
          ..where((tbl) => tbl.isTombstoned.equals(false))
          ..orderBy([(tbl) => OrderingTerm.desc(tbl.watchedAt)]))
        .get();
  }

  // --- Offline Ratings ---
  Future<void> upsertOfflineRating(OfflineRatingsCompanion rating) async {
    await into(offlineRatings).insertOnConflictUpdate(rating);
  }

  Future<List<OfflineRatingRow>> getOfflineRatings() async {
    return await select(offlineRatings).get();
  }

  Future<OfflineRatingRow?> getOfflineRatingForTitle(String titleId) async {
    return await (select(offlineRatings)..where((tbl) => tbl.titleId.equals(titleId))).getSingleOrNull();
  }

  // --- Offline User Title States ---
  Future<void> upsertOfflineTitleState(OfflineUserTitleStatesCompanion state) async {
    await into(offlineUserTitleStates).insertOnConflictUpdate(state);
  }

  Future<OfflineUserTitleStateRow?> getOfflineTitleState(String titleId) async {
    return await (select(offlineUserTitleStates)..where((tbl) => tbl.titleId.equals(titleId))).getSingleOrNull();
  }

  Future<List<OfflineUserTitleStateRow>> getOfflineFavorites() async {
    return await (select(offlineUserTitleStates)..where((tbl) => tbl.isFavorite.equals(true))).get();
  }

  // --- Offline Notes ---
  Future<void> upsertOfflineNote(OfflineNotesCompanion note) async {
    await into(offlineNotes).insertOnConflictUpdate(note);
  }

  Future<List<OfflineNoteRow>> getOfflineNotes() async {
    return await select(offlineNotes).get();
  }
}

LazyDatabase _openConnection() {
  return LazyDatabase(() async {
    if (Platform.environment.containsKey('FLUTTER_TEST')) {
      return NativeDatabase.memory();
    }
    try {
      final dbFolder = await getApplicationDocumentsDirectory();
      final file = File(p.join(dbFolder.path, 'cinevault_local.sqlite'));
      return NativeDatabase.createInBackground(file);
    } catch (_) {
      return NativeDatabase.memory();
    }
  });
}
