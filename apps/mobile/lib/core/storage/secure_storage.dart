// CineVault OS — Secure Storage Adapter
// Safely manages authentication tokens utilizing platform keychains (CAT-2 isolation)

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureStorageService {
  final FlutterSecureStorage _storage;

  static const String _accessTokenKey = 'cv_access_token';
  static const String _refreshTokenKey = 'cv_refresh_token';
  static const String _userIdKey = 'cv_authenticated_user_id';
  static const String _emailKey = 'cv_authenticated_email';
  static const String _rolesKey = 'cv_authenticated_roles';

  SecureStorageService({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
    required String userId,
    String? email,
    List<String>? roles,
  }) async {
    await _storage.write(key: _accessTokenKey, value: accessToken);
    await _storage.write(key: _refreshTokenKey, value: refreshToken);
    await _storage.write(key: _userIdKey, value: userId);
    if (email != null) {
      await _storage.write(key: _emailKey, value: email);
    }
    if (roles != null) {
      await _storage.write(key: _rolesKey, value: roles.join(','));
    }
  }

  Future<String?> getAccessToken() async {
    return await _storage.read(key: _accessTokenKey);
  }

  Future<String?> getRefreshToken() async {
    return await _storage.read(key: _refreshTokenKey);
  }

  Future<String?> getUserId() async {
    return await _storage.read(key: _userIdKey);
  }

  Future<String?> getEmail() async {
    return await _storage.read(key: _emailKey);
  }

  Future<List<String>?> getRoles() async {
    final raw = await _storage.read(key: _rolesKey);
    if (raw == null || raw.isEmpty) return null;
    return raw.split(',').where((r) => r.isNotEmpty).toList();
  }

  Future<void> clearSession() async {
    await _storage.delete(key: _accessTokenKey);
    await _storage.delete(key: _refreshTokenKey);
    await _storage.delete(key: _userIdKey);
    await _storage.delete(key: _emailKey);
    await _storage.delete(key: _rolesKey);
  }
}

