// CineVault OS — Control Room Repository Abstract Interface

import '../entities/control_room.dart';

abstract class ControlRoomRepository {
  Future<ControlRoomSummaryEntity> getSummaryStats();
  Future<List<ReconciliationCandidateEntity>> listCandidates();
  Future<CandidateDetailEntity> getCandidateDetail(String candidateId);
  Future<void> promoteCandidate(
    String candidateId, {
    required String rationale,
    Map<String, dynamic>? overrideFields,
  });
  Future<void> rejectCandidate(
    String candidateId, {
    required String rationale,
  });
  Future<List<AuditLogEntryEntity>> listAuditLogs({int limit = 50, int offset = 0});
}
