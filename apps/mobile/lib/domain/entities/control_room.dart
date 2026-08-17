// CineVault OS — Control Room Curation Domain Entities
// Implements CAT-6 Curation, Candidate Inspection & Audit Log Models

class ControlRoomSummaryEntity {
  final int pendingCandidates;
  final int pendingAiProposals;
  final int pendingQuarantineRecords;
  final int promotedCanonicalRecords;

  const ControlRoomSummaryEntity({
    required this.pendingCandidates,
    required this.pendingAiProposals,
    required this.pendingQuarantineRecords,
    required this.promotedCanonicalRecords,
  });

  factory ControlRoomSummaryEntity.fromJson(Map<String, dynamic> json) {
    return ControlRoomSummaryEntity(
      pendingCandidates: json['pending_reconciliation_candidates'] ?? 0,
      pendingAiProposals: json['pending_ai_proposals'] ?? 0,
      pendingQuarantineRecords: json['pending_quarantine_records'] ?? 0,
      promotedCanonicalRecords: json['promoted_canonical_records'] ?? 0,
    );
  }
}

class ReconciliationCandidateEntity {
  final String candidateId;
  final String sourceProvider;
  final String suggestedAction;
  final double matchConfidence;
  final String status;

  const ReconciliationCandidateEntity({
    required this.candidateId,
    required this.sourceProvider,
    required this.suggestedAction,
    required this.matchConfidence,
    required this.status,
  });

  factory ReconciliationCandidateEntity.fromJson(Map<String, dynamic> json) {
    return ReconciliationCandidateEntity(
      candidateId: json['candidate_id'] ?? '',
      sourceProvider: json['source_provider'] ?? '',
      suggestedAction: json['suggested_action'] ?? 'REQUIRES_REVIEW',
      matchConfidence: (json['match_confidence'] as num?)?.toDouble() ?? 0.0,
      status: json['status'] ?? 'PENDING_REVIEW',
    );
  }
}

class CandidateDetailEntity {
  final String candidateId;
  final String providerName;
  final String externalId;
  final String? candidateTitleId;
  final double matchConfidence;
  final String matchRuleId;
  final String decisionStatus;
  final Map<String, dynamic> evidenceSummary;
  final String createdAt;

  const CandidateDetailEntity({
    required this.candidateId,
    required this.providerName,
    required this.externalId,
    this.candidateTitleId,
    required this.matchConfidence,
    required this.matchRuleId,
    required this.decisionStatus,
    required this.evidenceSummary,
    required this.createdAt,
  });

  factory CandidateDetailEntity.fromJson(Map<String, dynamic> json) {
    return CandidateDetailEntity(
      candidateId: json['candidate_id'] ?? '',
      providerName: json['provider_name'] ?? '',
      externalId: json['external_id'] ?? '',
      candidateTitleId: json['candidate_title_id'],
      matchConfidence: (json['match_confidence'] as num?)?.toDouble() ?? 0.0,
      matchRuleId: json['match_rule_id'] ?? '',
      decisionStatus: json['decision_status'] ?? 'PENDING',
      evidenceSummary: (json['evidence_summary'] as Map<String, dynamic>?) ?? {},
      createdAt: json['created_at']?.toString() ?? '',
    );
  }
}

class AuditLogEntryEntity {
  final String eventId;
  final String timestamp;
  final String eventType;
  final String actorId;
  final String? targetId;
  final Map<String, dynamic> details;
  final String integrityHash;

  const AuditLogEntryEntity({
    required this.eventId,
    required this.timestamp,
    required this.eventType,
    required this.actorId,
    this.targetId,
    required this.details,
    required this.integrityHash,
  });

  factory AuditLogEntryEntity.fromJson(Map<String, dynamic> json) {
    return AuditLogEntryEntity(
      eventId: json['event_id'] ?? '',
      timestamp: json['timestamp'] ?? '',
      eventType: json['event_type'] ?? '',
      actorId: json['actor_id'] ?? '',
      targetId: json['target_id'],
      details: (json['details'] as Map<String, dynamic>?) ?? {},
      integrityHash: json['integrity_hash'] ?? '',
    );
  }
}
