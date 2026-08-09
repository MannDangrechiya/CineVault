// CineVault OS — Auth Riverpod Provider & State Management (Phase 9.8 — P3 Fix)
// Strict client-side RBAC guards and session state management.

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/repositories/auth_repository_impl.dart';
import '../../domain/entities/auth_session.dart';
import '../../domain/repositories/auth_repository.dart';

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepositoryImpl();
});

class AuthState {
  final bool isAuthenticated;
  final bool isLoading;
  final String? errorMessage;
  final AuthSessionEntity? session;

  const AuthState({
    this.isAuthenticated = false,
    this.isLoading = false,
    this.errorMessage,
    this.session,
  });

  bool get isCurator {
    if (!isAuthenticated || session == null) return false;
    final roles = session!.roles.map((r) => r.toLowerCase()).toSet();
    return roles.contains('curator') || roles.contains('systemadmin') || roles.contains('system_admin');
  }

  bool get isSystemAdmin {
    if (!isAuthenticated || session == null) return false;
    final roles = session!.roles.map((r) => r.toLowerCase()).toSet();
    return roles.contains('systemadmin') || roles.contains('system_admin');
  }

  AuthState copyWith({
    bool? isAuthenticated,
    bool? isLoading,
    String? errorMessage,
    AuthSessionEntity? session,
  }) {
    return AuthState(
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      isLoading: isLoading ?? this.isLoading,
      errorMessage: errorMessage,
      session: session ?? this.session,
    );
  }
}

class AuthNotifier extends StateNotifier<AuthState> {
  final AuthRepository _repository;

  AuthNotifier(this._repository) : super(const AuthState()) {
    checkSession();
  }

  Future<void> checkSession() async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final session = await _repository.getStoredSession();
      if (session != null) {
        state = state.copyWith(
          isAuthenticated: true,
          isLoading: false,
          session: session,
        );
      } else {
        state = state.copyWith(
          isAuthenticated: false,
          isLoading: false,
          session: null,
        );
      }
    } catch (e) {
      // Strict security: Any session read error strictly invalidates authentication.
      state = state.copyWith(
        isAuthenticated: false,
        isLoading: false,
        session: null,
        errorMessage: e.toString(),
      );
    }
  }

  Future<bool> login(String email, String password) async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final session = await _repository.login(email, password);
      state = state.copyWith(
        isAuthenticated: true,
        isLoading: false,
        session: session,
      );
      return true;
    } catch (e) {
      state = state.copyWith(
        isAuthenticated: false,
        isLoading: false,
        session: null,
        errorMessage: 'Invalid credentials or login failed.',
      );
      return false;
    }
  }

  bool canAccessControlRoom() {
    return state.isCurator;
  }

  Future<void> logout() async {
    await _repository.logout();
    state = const AuthState(isAuthenticated: false);
  }

  void handle401Unauthorized() {
    _repository.logout();
    state = const AuthState(
      isAuthenticated: false,
      errorMessage: 'Authentication session expired. Please log in again.',
    );
  }

  void handle403Forbidden() {
    state = state.copyWith(
      errorMessage: 'Access denied: Curator or SystemAdmin role required.',
    );
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final repository = ref.watch(authRepositoryProvider);
  return AuthNotifier(repository);
});
