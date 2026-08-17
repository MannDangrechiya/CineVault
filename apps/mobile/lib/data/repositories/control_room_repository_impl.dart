// CineVault OS — Control Room Repository Implementation

import '../../domain/entities/control_room.dart';
import '../../domain/repositories/control_room_repository.dart';
import '../remote/control_room_remote_datasource.dart';

class ControlRoomRepositoryImpl implements ControlRoomRepository {
  final ControlRoomRemoteDatasource _remoteDatasource;

  ControlRoomRepositoryImpl({ControlRoomRemoteDatasource? remoteDatasource})
      : _remoteDatasource = remoteDatasource ?? ControlRoomRemoteDatasourceImpl();

  @override
  Future<ControlRoomSummaryEntity> getSummaryStats() async {
    final raw = await _remoteDatasource.fetchSummaryStats();
    return ControlRoomSummaryEntity.fromJson(raw);
  }

  @override
  Future<List<ReconciliationCandidateEntity>> listCandidates() async {
    final rawList = await _remoteDatasource.fetchCandidates();
    return rawList
        .map((item) => ReconciliationCandidateEntity.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  @override
  Future<CandidateDetailEntity> getCandidateDetail(String candidateId) async {
    final raw = await _remoteDatasource.fetchCandidateDetail(candidateId);
    return CandidateDetailEntity.fromJson(raw);
  }

  @override
  Future<void> promoteCandidate(
    String candidateId, {
    required String rationale,
    Map<String, dynamic>? overrideFields,
  }) async {
    await _remoteDatasource.promoteCandidate(
      candidateId,
      rationale: rationale,
      overrideFields: overrideFields,
    );
  }

  @override
  Future<void> rejectCandidate(
    String candidateId, {
    required String rationale,
  }) async {
    await _remoteDatasource.rejectCandidate(
      candidateId,
      rationale: rationale,
    );
  }

  @override
  Future<List<AuditLogEntryEntity>> listAuditLogs({int limit = 50, int offset = 0}) async {
    final rawList = await _remoteDatasource.fetchAuditLogs(limit: limit, offset: offset);
    return rawList
        .map((item) => AuditLogEntryEntity.fromJson(item as Map<String, dynamic>))
        .toList();
  }
}
