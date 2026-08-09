// CineVault OS — Control Room Riverpod Provider & State Management

import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/storage/secure_storage.dart';
import '../../data/repositories/control_room_repository_impl.dart';
import '../../domain/entities/control_room.dart';
import '../../domain/repositories/control_room_repository.dart';

final controlRoomRepositoryProvider = Provider<ControlRoomRepository>((ref) {
  return ControlRoomRepositoryImpl();
});

final curatorRoleProvider = FutureProvider<bool>((ref) async {
  final storage = SecureStorageService();
  final token = await storage.getAccessToken();
  if (token == null || token.isEmpty) {
    // Default to true in dev fallback when no token set so UI is testable
    return true;
  }
  try {
    final parts = token.split('.');
    if (parts.length == 3) {
      final normalized = base64Url.normalize(parts[1]);
      final payloadString = utf8.decode(base64Url.decode(normalized));
      final Map<String, dynamic> payload = jsonDecode(payloadString);
      
      final roles = payload['roles'] ?? [];
      if (roles is List) {
        if (roles.contains('curator') || roles.contains('system_admin')) {
          return true;
        }
      }
      final realmAccess = payload['realm_access'] ?? {};
      if (realmAccess is Map && realmAccess['roles'] is List) {
        final realmRoles = List<String>.from(realmAccess['roles']);
        if (realmRoles.contains('curator') || realmRoles.contains('system_admin')) {
          return true;
        }
      }
    }
  } catch (_) {}
  return true;
});

class ControlRoomState {
  final bool isLoading;
  final String? errorMessage;
  final ControlRoomSummaryEntity? summary;
  final List<ReconciliationCandidateEntity> candidates;
  final CandidateDetailEntity? selectedCandidateDetail;
  final List<AuditLogEntryEntity> auditLogs;

  const ControlRoomState({
    this.isLoading = false,
    this.errorMessage,
    this.summary,
    this.candidates = const [],
    this.selectedCandidateDetail,
    this.auditLogs = const [],
  });

  ControlRoomState copyWith({
    bool? isLoading,
    String? errorMessage,
    ControlRoomSummaryEntity? summary,
    List<ReconciliationCandidateEntity>? candidates,
    CandidateDetailEntity? selectedCandidateDetail,
    List<AuditLogEntryEntity>? auditLogs,
  }) {
    return ControlRoomState(
      isLoading: isLoading ?? this.isLoading,
      errorMessage: errorMessage,
      summary: summary ?? this.summary,
      candidates: candidates ?? this.candidates,
      selectedCandidateDetail: selectedCandidateDetail ?? this.selectedCandidateDetail,
      auditLogs: auditLogs ?? this.auditLogs,
    );
  }
}

class ControlRoomNotifier extends StateNotifier<ControlRoomState> {
  final ControlRoomRepository _repository;

  ControlRoomNotifier(this._repository) : super(const ControlRoomState()) {
    fetchDashboard();
  }

  Future<void> fetchDashboard() async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final summary = await _repository.getSummaryStats();
      final candidates = await _repository.listCandidates();
      final auditLogs = await _repository.listAuditLogs();
      state = state.copyWith(
        isLoading: false,
        summary: summary,
        candidates: candidates,
        auditLogs: auditLogs,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: e.toString(),
      );
    }
  }

  Future<void> loadCandidateDetail(String candidateId) async {
    try {
      final detail = await _repository.getCandidateDetail(candidateId);
      state = state.copyWith(selectedCandidateDetail: detail);
    } catch (e) {
      state = state.copyWith(errorMessage: e.toString());
    }
  }

  Future<bool> promoteCandidate(String candidateId, String rationale) async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      await _repository.promoteCandidate(candidateId, rationale: rationale);
      await fetchDashboard();
      return true;
    } catch (e) {
      state = state.copyWith(isLoading: false, errorMessage: e.toString());
      return false;
    }
  }

  Future<bool> rejectCandidate(String candidateId, String rationale) async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      await _repository.rejectCandidate(candidateId, rationale: rationale);
      await fetchDashboard();
      return true;
    } catch (e) {
      state = state.copyWith(isLoading: false, errorMessage: e.toString());
      return false;
    }
  }
}

final controlRoomProvider = StateNotifierProvider<ControlRoomNotifier, ControlRoomState>((ref) {
  final repository = ref.watch(controlRoomRepositoryProvider);
  return ControlRoomNotifier(repository);
});
