// CineVault OS — Auth Repository Implementation

import '../../core/storage/secure_storage.dart';
import '../../domain/entities/auth_session.dart';
import '../../domain/repositories/auth_repository.dart';
import '../remote/auth_remote_datasource.dart';

class AuthRepositoryImpl implements AuthRepository {
  final AuthRemoteDatasource _remoteDatasource;
  final SecureStorageService _secureStorage;

  AuthRepositoryImpl({
    AuthRemoteDatasource? remoteDatasource,
    SecureStorageService? secureStorage,
  })  : _remoteDatasource = remoteDatasource ?? AuthRemoteDatasourceImpl(),
        _secureStorage = secureStorage ?? SecureStorageService();

  @override
  Future<AuthSessionEntity> login(String email, String password) async {
    final raw = await _remoteDatasource.login(email, password);
    final session = AuthSessionEntity.fromJson(raw);

    await _secureStorage.saveTokens(
      accessToken: session.accessToken,
      refreshToken: session.refreshToken,
      userId: session.userId,
    );

    return session;
  }

  @override
  Future<void> logout() async {
    await _secureStorage.clearSession();
  }

  @override
  Future<AuthSessionEntity?> getStoredSession() async {
    final token = await _secureStorage.getAccessToken();
    final refreshToken = await _secureStorage.getRefreshToken();
    final userId = await _secureStorage.getUserId();

    if (token == null || token.isEmpty) {
      return null;
    }

    return AuthSessionEntity(
      accessToken: token,
      refreshToken: refreshToken ?? '',
      userId: userId ?? '',
      email: 'user@cinevault.org',
      roles: const ['authenticated_user'],
    );
  }
}
