// CineVault OS — Import Remote Datasource (Part 3.9)
// Covers /v1/personal/import/{preview,apply} — text-based CSV/JSON/plain-
// text import, matching apps/web/src/lib/api/import.ts's previewImport/
// applyImport. Deliberately does NOT port uploadImportFile/extractPdfText:
// those are multipart file-upload endpoints (raw fetch + FormData on web);
// PDF extraction in particular is a server-side-only convenience with no
// mobile-specific value beyond what CSV/JSON/plain-text import already
// covers, and PLAN.md 3.9 marks this whole item lowest-priority — scoped to
// the file formats a mobile file picker can read as plain text directly.

import '../../core/config/api_config.dart';
import '../../core/network/api_client.dart';
import '../../domain/entities/import_data.dart';

class ImportRemoteDatasource {
  final ApiClient _apiClient;

  ImportRemoteDatasource({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  Future<ImportPreviewResult> previewImport(List<ImportItem> items) async {
    final response = await _apiClient.dio.post(
      ApiConfig.importPreviewEndpoint,
      data: {'items': items.map((i) => i.toJson()).toList()},
    );
    return ImportPreviewResult.fromJson(response.data);
  }

  Future<ImportApplyResult> applyImport({
    required List<ImportItem> items,
    String conflictStrategy = 'KEEP_EXISTING',
  }) async {
    final response = await _apiClient.dio.post(
      ApiConfig.importApplyEndpoint,
      data: {
        'items': items.map((i) => i.toJson()).toList(),
        'conflict_strategy': conflictStrategy,
      },
    );
    return ImportApplyResult.fromJson(response.data);
  }
}
