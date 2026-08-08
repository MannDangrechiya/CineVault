// CineVault OS — Network API Client Wrapper
// Wraps Dio with Bearer auth token injection, correlation headers, and standardized error parsing

import 'package:dio/dio.dart';
import '../config/api_config.dart';
import '../error/failures.dart';
import '../storage/secure_storage.dart';
import '../utils/uuid_util.dart';

class ApiClient {
  final Dio _dio;
  final SecureStorageService _secureStorage;

  ApiClient({Dio? dio, SecureStorageService? secureStorage})
      : _dio = dio ??
            Dio(
              BaseOptions(
                baseUrl: ApiConfig.baseUrl,
                connectTimeout: ApiConfig.connectTimeout,
                receiveTimeout: ApiConfig.receiveTimeout,
                headers: {
                  'Content-Type': 'application/json',
                  'Accept': 'application/json',
                },
              ),
            ),
        _secureStorage = secureStorage ?? SecureStorageService() {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          // Inject Correlation ID header for observability
          options.headers['X-Correlation-ID'] = UuidUtil.generateCorrelationId();

          // Inject Bearer token if session exists
          final token = await _secureStorage.getAccessToken();
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }

          return handler.next(options);
        },
        onError: (DioException error, handler) {
          return handler.next(error);
        },
      ),
    );
  }

  Dio get dio => _dio;

  /// Helper to convert DioException into application Failures
  Failure mapDioErrorToFailure(DioException error) {
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.connectionError) {
      return const NetworkFailure();
    }

    final response = error.response;
    if (response == null) {
      return const ServerFailure('No response received from CineVault gateway.');
    }

    final statusCode = response.statusCode ?? 500;
    final message = _extractErrorMessage(response.data);

    switch (statusCode) {
      case 400:
        return ValidationFailure(message ?? 'Invalid request parameters.', statusCode);
      case 401:
        return UnauthorizedFailure(message ?? 'Authentication session expired.', statusCode);
      case 403:
        return ForbiddenFailure(message ?? 'Access denied.', statusCode);
      case 404:
        return NotFoundFailure(message ?? 'Resource not found.', statusCode);
      case 409:
        return ConflictFailure(message ?? 'Conflict detected.', statusCode);
      case 422:
        return ValidationFailure(message ?? 'Validation failed.', statusCode);
      case 500:
      default:
        return ServerFailure(message ?? 'Server error occurred.', statusCode);
    }
  }

  String? _extractErrorMessage(dynamic responseData) {
    if (responseData is Map<String, dynamic>) {
      if (responseData.containsKey('detail')) {
        final detail = responseData['detail'];
        if (detail is String) return detail;
        if (detail is List && detail.isNotEmpty) {
          final first = detail.first;
          if (first is Map && first.containsKey('msg')) {
            return first['msg'].toString();
          }
        }
      }
      if (responseData.containsKey('message')) {
        return responseData['message'].toString();
      }
    }
    return null;
  }
}
