// CineVault OS — Auth Repository Interface

import '../entities/auth_session.dart';

abstract class AuthRepository {
  Future<AuthSessionEntity> login(String email, String password);
  Future<AuthSessionEntity> register(String email, String password, String inviteCode);
  Future<AuthSessionEntity> refreshSession();
  Future<void> logout();
  Future<AuthSessionEntity?> getStoredSession();
}
