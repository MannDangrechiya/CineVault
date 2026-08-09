// CineVault OS — Control Room Remote Datasource
// Connects to privileged curation endpoints at /internal/v1/control-room/*

import '../../core/network/api_client.dart';

abstract class ControlRoomRemoteDatasource {
  Future<Map<String, dynamic>> fetchSummaryStats();
  Future<List<dynamic>> fetchCandidates();
  Future<Map<String, dynamic>> fetchCandidateDetail(String candidateId);
  Future<Map<String, dynamic>> promoteCandidate(
    String candidateId, {
    required String rationale,
    Map<String, dynamic>? overrideFields,
  });
  Future<Map<String, dynamic>> rejectCandidate(
    String candidateId, {
    required String rationale,
  });
  Future<List<dynamic>> fetchAuditLogs({int limit = 50, int offset = 0});
}

class ControlRoomRemoteDatasourceImpl implements ControlRoomRemoteDatasource {
  final ApiClient _apiClient;

  ControlRoomRemoteDatasourceImpl({ApiClient? apiClient})
      : _apiClient = apiClient ?? ApiClient();

  @override
  Future<Map<String, dynamic>> fetchSummaryStats() async {
    try {
      final response = await _apiClient.dio.get('/internal/v1/control-room/stats');
      return response.data as Map<String, dynamic>;
    } catch (e) {
      rethrow;
    }
  }

  @override
  Future<List<dynamic>> fetchCandidates() async {
    try {
      final response = await _apiClient.dio.get('/internal/v1/control-room/candidates');
      return response.data as List<dynamic>;
    } catch (e) {
      rethrow;
    }
  }

  @override
  Future<Map<String, dynamic>> fetchCandidateDetail(String candidateId) async {
    try {
      final response = await _apiClient.dio.get('/internal/v1/control-room/candidates/$candidateId');
      return response.data as Map<String, dynamic>;
    } catch (e) {
      rethrow;
    }
  }

  @override
  Future<Map<String, dynamic>> promoteCandidate(
    String candidateId, {
    required String rationale,
    Map<String, dynamic>? overrideFields,
  }) async {
    try {
      final response = await _apiClient.dio.post(
        '/internal/v1/control-room/candidates/$candidateId/promote',
        data: {
          'rationale': rationale,
          if (overrideFields != null) 'override_fields': overrideFields,
        },
      );
      return response.data as Map<String, dynamic>;
    } catch (e) {
      rethrow;
    }
  }

  @override
  Future<Map<String, dynamic>> rejectCandidate(
    String candidateId, {
    required String rationale,
  }) async {
    try {
      final response = await _apiClient.dio.post(
        '/internal/v1/control-room/candidates/$candidateId/reject',
        data: {
          'rationale': rationale,
        },
      );
      return response.data as Map<String, dynamic>;
    } catch (e) {
      rethrow;
    }
  }

  @override
  Future<List<dynamic>> fetchAuditLogs({int limit = 50, int offset = 0}) async {
    try {
      final response = await _apiClient.dio.get(
        '/internal/v1/control-room/audit-log',
        queryParameters: {
          'limit': limit,
          'offset': offset,
        },
      );
      return response.data as List<dynamic>;
    } catch (e) {
      rethrow;
    }
  }
}
