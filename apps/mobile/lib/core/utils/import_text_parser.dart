// CineVault OS — Import Text Parser (Part 3.9)
// Ports apps/web/src/lib/api/import.ts's parseImportText 1:1: detects and
// parses JSON, CSV (Letterboxd/Trakt-style export), or unstructured plain
// text (numbered/bulleted watch lists, star ratings, "X/5"·"X/10" scores).
// PDF text-layer extraction is server-side only and not ported here — see
// import_remote_datasource.dart's header comment for why it's out of scope
// for this pass.

import 'dart:convert';
import '../../domain/entities/import_data.dart';

enum ImportFormatHint { auto, csv, json, notes }

class ImportTextParser {
  ImportTextParser._();

  static List<ImportItem> parse(String rawText, {ImportFormatHint formatHint = ImportFormatHint.auto}) {
    final trimmed = rawText.trim();
    if (trimmed.isEmpty) return const [];

    if (formatHint == ImportFormatHint.json ||
        (formatHint == ImportFormatHint.auto && (trimmed.startsWith('[') || trimmed.startsWith('{')))) {
      final parsed = _tryParseJson(trimmed);
      if (parsed != null) return parsed;
    }

    if (formatHint == ImportFormatHint.csv ||
        (formatHint == ImportFormatHint.auto && trimmed.contains(',') && trimmed.contains(RegExp(r'[\r\n]')))) {
      final parsed = _tryParseCsv(trimmed);
      if (parsed != null) return parsed;
    }

    return _parsePlainText(trimmed);
  }

  static List<ImportItem>? _tryParseJson(String trimmed) {
    try {
      final decoded = jsonDecode(trimmed);
      final list = decoded is List ? decoded : [decoded];
      final items = <ImportItem>[];
      for (final raw in list) {
        if (raw is! Map) continue;
        final map = raw.cast<String, dynamic>();
        final title = (map['canonical_title'] ?? map['title'] ?? map['name'] ?? '').toString().trim();
        if (title.isEmpty) continue;
        items.add(ImportItem(
          canonicalTitle: title,
          productionYear: _asInt(map['production_year'] ?? map['year']),
          ratingValue: _asInt(map['rating_value'] ?? map['rating']),
          watchedAt: (map['watched_at'] ?? map['date'])?.toString(),
          manualStatusOverride: (map['manual_status_override'] ?? map['status'] ?? 'COMPLETED').toString(),
          isFavorite: map['is_favorite'] == true || map['favorite'] == true,
          notes: map['notes']?.toString(),
        ));
      }
      return items;
    } catch (_) {
      return null;
    }
  }

  static List<ImportItem>? _tryParseCsv(String trimmed) {
    final lines = trimmed.split(RegExp(r'\r?\n')).where((l) => l.trim().isNotEmpty).toList();
    if (lines.length <= 1) return null;

    final headerLine = lines[0].toLowerCase();
    if (!headerLine.contains('title') && !headerLine.contains('name')) return null;

    final headers = lines[0].split(',').map((h) => h.trim().toLowerCase().replaceAll('"', '')).toList();
    final titleIdx = headers.indexWhere((h) => h == 'title' || h == 'name' || h == 'film');
    if (titleIdx == -1) return null;
    final yearIdx = headers.indexWhere((h) => h == 'year' || h == 'release year');
    final ratingIdx = headers.indexWhere((h) => h == 'rating' || h == 'rating10' || h == 'score');
    final dateIdx = headers.indexWhere((h) => h.contains('date') || h == 'watched_at' || h == 'watched date');

    final results = <ImportItem>[];
    for (var i = 1; i < lines.length; i++) {
      final cols = lines[i].split(',').map((c) => c.trim().replaceAll(RegExp(r'^"|"$'), '')).toList();
      if (titleIdx >= cols.length) continue;
      final title = cols[titleIdx];
      if (title.isEmpty) continue;

      final year = (yearIdx != -1 && yearIdx < cols.length) ? int.tryParse(cols[yearIdx]) : null;
      final rating = (ratingIdx != -1 && ratingIdx < cols.length) ? double.tryParse(cols[ratingIdx]) : null;
      final date = (dateIdx != -1 && dateIdx < cols.length && cols[dateIdx].isNotEmpty) ? cols[dateIdx] : null;

      results.add(ImportItem(
        canonicalTitle: title,
        productionYear: year,
        ratingValue: rating?.round(),
        watchedAt: date,
        manualStatusOverride: 'COMPLETED',
      ));
    }
    return results.isEmpty ? null : results;
  }

  static List<ImportItem> _parsePlainText(String trimmed) {
    final lines = trimmed.split(RegExp(r'\r?\n')).where((l) => l.trim().isNotEmpty);
    final items = <ImportItem>[];

    for (final rawLine in lines) {
      var clean = rawLine.trim();
      // Strip leading list numbers/bullets: "1.", "1)", "-", "*", "•"
      clean = clean.replaceFirst(RegExp(r'^(\d+[.)]|-|\*|•)\s*'), '').trim();
      if (clean.isEmpty) continue;

      int? year;
      int? rating;
      String? notes;

      final starCount = '★'.allMatches(clean).length;
      if (starCount > 0) {
        rating = starCount;
        clean = clean.replaceAll(RegExp('★+'), '').trim();
      }

      final scoreMatch = RegExp(r'(\d+(?:\.\d+)?)\s*/\s*(5|10)').firstMatch(clean);
      if (scoreMatch != null) {
        final val = double.parse(scoreMatch.group(1)!);
        final max = double.parse(scoreMatch.group(2)!);
        rating = max == 10 ? (val / 2).round() : val.round();
        clean = clean.replaceFirst(scoreMatch.group(0)!, '').trim();
      }

      final yearMatch = RegExp(r'[(\[]\s*(18\d\d|19\d\d|20\d\d)\s*[)\]]').firstMatch(clean);
      if (yearMatch != null) {
        year = int.parse(yearMatch.group(1)!);
        clean = clean.replaceFirst(yearMatch.group(0)!, '').trim();
      }

      if (clean.contains(' - ')) {
        final parts = clean.split(' - ');
        clean = parts.first.trim();
        notes = parts.sublist(1).join(' - ').trim();
      }

      // Strip trailing commas/colons/semicolons/dashes left over once the
      // year and score above were already consumed (e.g. "Parasite (2019) -"
      // has no " - "-with-content left to split on once both are stripped).
      clean = clean.replaceAll(RegExp(r'[,:;-]+$'), '').trim();

      if (clean.isNotEmpty) {
        items.add(ImportItem(
          canonicalTitle: clean,
          productionYear: year,
          ratingValue: rating,
          notes: notes,
          manualStatusOverride: 'COMPLETED',
          watchedAt: DateTime.now().toIso8601String(),
        ));
      }
    }

    return items;
  }

  static int? _asInt(dynamic value) {
    if (value == null) return null;
    if (value is num) return value.toInt();
    return int.tryParse(value.toString());
  }
}
