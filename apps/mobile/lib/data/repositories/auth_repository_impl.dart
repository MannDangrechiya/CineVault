// CineVault OS — Auth Repository Implementation

import 'dart:convert';
import '../../core/storage/secure_storage.dart';
import '../../domain/entities/auth_session.dart';
import '../../domain/repositories/auth_repository.dart';
import '../local/app_database.dart';
import '../remote/auth_remote_datasource.dart';

class AuthRepositoryImpl implements AuthRepository {
  final AuthRemoteDatasource _remoteDatasource;
  final SecureStorageService _secureStorage;
  final AppDatabase? _db;

  AuthRepositoryImpl({
    AuthRemoteDatasource? remoteDatasource,
    SecureStorageService? secureStorage,
    AppDatabase? db,
  })  : _remoteDatasource = remoteDatasource ?? AuthRemoteDatasourceImpl(),
        _secureStorage = secureStorage ?? SecureStorageService(),
        _db = db;

  @override
  Future<AuthSessionEntity> login(String email, String password) async {
    final raw = await _remoteDatasource.login(email, password);
    final session = AuthSessionEntity.fromJson(raw);

    await _secureStorage.saveTokens(
      accessToken: session.accessToken,
      refreshToken: session.refreshToken,
      userId: session.userId,
      email: session.email,
      roles: session.roles,
    );

    return session;
  }

  @override
  Future<AuthSessionEntity> register(String email, String password, String inviteCode) async {
    final raw = await _remoteDatasource.register(email, password, inviteCode);
    final session = AuthSessionEntity.fromJson(raw);

    await _secureStorage.saveTokens(
      accessToken: session.accessToken,
      refreshToken: session.refreshToken,
      userId: session.userId,
      email: session.email,
      roles: session.roles,
    );

    return session;
  }

  @override
  Future<AuthSessionEntity> refreshSession() async {
    final refreshToken = await _secureStorage.getRefreshToken();
    if (refreshToken == null || refreshToken.isEmpty) {
      throw Exception('No refresh token stored');
    }
    final raw = await _remoteDatasource.refresh(refreshToken);
    final session = AuthSessionEntity.fromJson(raw);

    await _secureStorage.saveTokens(
      accessToken: session.accessToken,
      refreshToken: session.refreshToken,
      userId: session.userId,
      email: session.email,
      roles: session.roles,
    );

    return session;
  }

  @override
  Future<void> logout() async {
    await _secureStorage.clearSession();
    if (_db != null) {
      await _db.clearPersonalData();
    }
  }

  @override
  Future<AuthSessionEntity?> getStoredSession() async {
    final token = await _secureStorage.getAccessToken();
    final refreshToken = await _secureStorage.getRefreshToken();
    final userId = await _secureStorage.getUserId();
    String? email = await _secureStorage.getEmail();
    List<String>? roles = await _secureStorage.getRoles();

    if (token == null || token.isEmpty) {
      return null;
    }

    // Decode JWT payload claims as authoritative fallback
    if ((email == null || roles == null) && token.contains('.')) {
      try {
        final parts = token.split('.');
        if (parts.length == 3) {
          final normalized = base64Url.normalize(parts[1]);
          final payloadString = utf8.decode(base64Url.decode(normalized));
          final Map<String, dynamic> payload = jsonDecode(payloadString);
          email ??= payload['email'] as String? ?? payload['preferred_username'] as String?;
          if (roles == null) {
            if (payload['roles'] is List) {
              roles = List<String>.from(payload['roles']);
            } else if (payload['realm_access'] is Map && payload['realm_access']['roles'] is List) {
              roles = List<String>.from(payload['realm_access']['roles']);
            }
          }
        }
      } catch (_) {}
    }

    return AuthSessionEntity(
      accessToken: token,
      refreshToken: refreshToken ?? '',
      userId: userId ?? '',
      email: email ?? 'user@cinevault.org',
      roles: roles ?? const ['authenticated_user'],
    );
  }
}

