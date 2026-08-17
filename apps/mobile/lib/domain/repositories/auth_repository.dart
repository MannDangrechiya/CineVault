// CineVault OS — Auth Repository Interface

import '../entities/auth_session.dart';

abstract class AuthRepository {
  Future<AuthSessionEntity> login(String email, String password);
  Future<void> logout();
  Future<AuthSessionEntity?> getStoredSession();
}
