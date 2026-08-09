// CineVault OS — Control Room Curator Screen Widget & Role Gating Tests (Phase 9.7)

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:cinevault_client/domain/entities/control_room.dart';
import 'package:cinevault_client/domain/repositories/control_room_repository.dart';
import 'package:cinevault_client/presentation/providers/control_room_provider.dart';
import 'package:cinevault_client/presentation/screens/control_room_screen.dart';

class FakeControlRoomRepository implements ControlRoomRepository {
  final ControlRoomSummaryEntity mockSummary;
  final List<ReconciliationCandidateEntity> mockCandidates;
  final List<AuditLogEntryEntity> mockAuditLogs;

  FakeControlRoomRepository({
    required this.mockSummary,
    required this.mockCandidates,
    required this.mockAuditLogs,
  });

  @override
  Future<ControlRoomSummaryEntity> getSummaryStats() async => mockSummary;

  @override
  Future<List<ReconciliationCandidateEntity>> listCandidates() async => mockCandidates;

  @override
  Future<CandidateDetailEntity> getCandidateDetail(String candidateId) async {
    return CandidateDetailEntity(
      candidateId: candidateId,
      providerName: 'KOBIS',
      externalId: '20192194',
      matchConfidence: 0.95,
      matchRuleId: 'RULE-EXACT-TITLE-YEAR',
      decisionStatus: 'PENDING',
      evidenceSummary: const {'title': 'Parasite', 'year': 2019},
      createdAt: '2026-08-09T00:00:00Z',
    );
  }

  @override
  Future<void> promoteCandidate(
    String candidateId, {
    required String rationale,
    Map<String, dynamic>? overrideFields,
  }) async {}

  @override
  Future<void> rejectCandidate(
    String candidateId, {
    required String rationale,
  }) async {}

  @override
  Future<List<AuditLogEntryEntity>> listAuditLogs({int limit = 50, int offset = 0}) async => mockAuditLogs;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  FlutterSecureStorage.setMockInitialValues({});

  const mockSummary = ControlRoomSummaryEntity(
    pendingCandidates: 5,
    pendingAiProposals: 2,
    pendingQuarantineRecords: 1,
    promotedCanonicalRecords: 42,
  );

  const mockCandidate = ReconciliationCandidateEntity(
    candidateId: 'CAND-001',
    sourceProvider: 'KOBIS',
    suggestedAction: 'MATCH_EXACT',
    matchConfidence: 0.95,
    status: 'PENDING_REVIEW',
  );

  const mockAuditLog = AuditLogEntryEntity(
    eventId: 'AUD-001',
    timestamp: '2026-08-09T10:00:00Z',
    eventType: 'PROMOTION_ACCEPTED',
    actorId: 'curator-user-1',
    targetId: 'CAND-001',
    details: {'rationale': 'Approved'},
    integrityHash: 'abc1234567890def1234567890def123',
  );

  testWidgets('ControlRoomScreen renders summary stats metrics and candidates list', (WidgetTester tester) async {
    final fakeRepo = FakeControlRoomRepository(
      mockSummary: mockSummary,
      mockCandidates: [mockCandidate],
      mockAuditLogs: [mockAuditLog],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          controlRoomRepositoryProvider.overrideWithValue(fakeRepo),
          curatorRoleProvider.overrideWith((ref) async => true),
        ],
        child: const MaterialApp(home: ControlRoomScreen()),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Control Room Curation'), findsOneWidget);
    expect(find.text('5'), findsOneWidget); // pending candidates count
    expect(find.text('42'), findsOneWidget); // promoted count
    expect(find.textContaining('CAND-001'), findsOneWidget);
    expect(find.text('KOBIS'), findsOneWidget);
    expect(find.text('Promote'), findsOneWidget);
    expect(find.text('Reject'), findsOneWidget);
  });

  testWidgets('ControlRoomScreen shows promote dialog and executes decision', (WidgetTester tester) async {
    final fakeRepo = FakeControlRoomRepository(
      mockSummary: mockSummary,
      mockCandidates: [mockCandidate],
      mockAuditLogs: [mockAuditLog],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          controlRoomRepositoryProvider.overrideWithValue(fakeRepo),
          curatorRoleProvider.overrideWith((ref) async => true),
        ],
        child: const MaterialApp(home: ControlRoomScreen()),
      ),
    );

    await tester.pumpAndSettle();

    await tester.tap(find.text('Promote'));
    await tester.pumpAndSettle();

    expect(find.text('Promote Candidate'), findsOneWidget);
    expect(find.text('Confirm Promote'), findsOneWidget);

    await tester.tap(find.text('Confirm Promote'));
    await tester.pumpAndSettle();

    expect(find.text('Promote Candidate'), findsNothing);
  });

  testWidgets('ControlRoomScreen displays access restricted when non-curator role', (WidgetTester tester) async {
    final fakeRepo = FakeControlRoomRepository(
      mockSummary: mockSummary,
      mockCandidates: [],
      mockAuditLogs: [],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          controlRoomRepositoryProvider.overrideWithValue(fakeRepo),
          curatorRoleProvider.overrideWith((ref) async => false),
        ],
        child: const MaterialApp(home: ControlRoomScreen()),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Access Restricted: Curator role required.'), findsOneWidget);
  });
}
