// CineVault OS — Drift Local Database (8.9, ADR-004)
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
  TextColumn get mutationType => text()(); // CREATE_WATCH_EVENT, SET_RATING, UPSERT_NOTE
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

  @override
  Set<Column> get primaryKey => {titleId};
}

@DataClassName('RecentSearchRow')
class RecentSearches extends Table {
  TextColumn get query => text()();
  TextColumn get searchedAt => text()();

  @override
  Set<Column> get primaryKey => {query};
}

// ------------------------------------------------------------------------
// App Database Class
// ------------------------------------------------------------------------

@DriftDatabase(tables: [OutboxMutations, CachedTitles, RecentSearches])
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

  // --- Recent Searches Queries ---
  Future<void> addRecentSearch(String queryText) async {
    await into(recentSearches).insertOnConflictUpdate(
      RecentSearchesCompanion.insert(
        query: queryText,
        searchedAt: DateTime.now().toIso8601String(),
      ),
    );
  }

  Future<List<RecentSearchRow>> getRecentSearches() async {
    return await (select(recentSearches)..orderBy([(tbl) => OrderingTerm.desc(tbl.searchedAt)])).get();
  }
}

LazyDatabase _openConnection() {
  return LazyDatabase(() async {
    final dbFolder = await getApplicationDocumentsDirectory();
    final file = File(p.join(dbFolder.path, 'cinevault_local.sqlite'));
    return NativeDatabase.createInBackground(file);
  });
}
