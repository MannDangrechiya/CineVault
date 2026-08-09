// CineVault OS — Auth Remote Datasource (Phase 9.8)

import '../../core/network/api_client.dart';

abstract class AuthRemoteDatasource {
  Future<Map<String, dynamic>> login(String email, String password);
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
}
