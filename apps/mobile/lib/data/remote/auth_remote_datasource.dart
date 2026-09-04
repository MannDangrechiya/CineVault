// CineVault OS — Auth Remote Datasource (Phase 9.8 & Phase 1 Native Auth)

import '../../core/network/api_client.dart';

abstract class AuthRemoteDatasource {
  Future<Map<String, dynamic>> login(String email, String password);
  Future<Map<String, dynamic>> register(String email, String password, String inviteCode);
  Future<Map<String, dynamic>> refresh(String refreshToken);
}

class AuthRemoteDatasourceImpl implements AuthRemoteDatasource {
  final ApiClient _apiClient;

  AuthRemoteDatasourceImpl({ApiClient? apiClient})
      : _apiClient = apiClient ?? ApiClient();

  @override
  Future<Map<String, dynamic>> login(String email, String password) async {
    try {
      final response = await _apiClient.dio.post(
        '/v1/auth/login',
        data: {
          'email': email,
          'password': password,
        },
      );
      return response.data as Map<String, dynamic>;
    } catch (e) {
      rethrow;
    }
  }

  @override
  Future<Map<String, dynamic>> register(String email, String password, String inviteCode) async {
    try {
      final response = await _apiClient.dio.post(
        '/v1/auth/register',
        data: {
          'email': email,
          'password': password,
          'invite_code': inviteCode,
        },
      );
      return response.data as Map<String, dynamic>;
    } catch (e) {
      rethrow;
    }
  }

  @override
  Future<Map<String, dynamic>> refresh(String refreshToken) async {
    try {
      final response = await _apiClient.dio.post(
        '/v1/auth/refresh',
        data: {
          'refresh_token': refreshToken,
        },
      );
      return response.data as Map<String, dynamic>;
    } catch (e) {
      rethrow;
    }
  }
}
