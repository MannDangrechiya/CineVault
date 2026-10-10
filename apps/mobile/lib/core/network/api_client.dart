// CineVault OS — Network API Client Wrapper
// Wraps Dio with Bearer auth token injection, correlation headers, and standardized error parsing

import 'package:dio/dio.dart';
import '../config/api_config.dart';
import '../error/failures.dart';
import '../storage/secure_storage.dart';
import '../utils/uuid_util.dart';

class ApiClient {
  final Dio _dio;
  final Dio _tokenRefreshDio;
  final SecureStorageService _secureStorage;
  final void Function()? onUnauthorized;
  Future<bool>? _refreshFuture;

  ApiClient({
    Dio? dio,
    Dio? tokenRefreshDio,
    SecureStorageService? secureStorage,
    this.onUnauthorized,
  })  : _dio = dio ??
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
        _tokenRefreshDio = tokenRefreshDio ??
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
        onError: (DioException error, handler) async {
          if (error.response?.statusCode == 401) {
            final requestPath = error.requestOptions.path;
            final isAuthEndpoint = requestPath.contains('/v1/auth/login') ||
                requestPath.contains('/v1/auth/register') ||
                requestPath.contains('/v1/auth/refresh');
            final isAlreadyRetried = error.requestOptions.extra['_retry'] == true;

            if (requestPath.contains('/v1/auth/refresh') || isAlreadyRetried) {
              // Refresh endpoint itself failed or already retried — clear session
              await _secureStorage.clearSession();
              onUnauthorized?.call();
            } else if (!isAuthEndpoint) {
              // Attempt transparent token refresh and retry original request
              final refreshed = await _refreshAccessToken();
              if (refreshed) {
                final newToken = await _secureStorage.getAccessToken();
                if (newToken != null && newToken.isNotEmpty) {
                  final retryOptions = error.requestOptions;
                  retryOptions.headers['Authorization'] = 'Bearer $newToken';
                  retryOptions.extra['_retry'] = true;

                  try {
                    final response = await _dio.fetch(retryOptions);
                    return handler.resolve(response);
                  } on DioException catch (retryError) {
                    final failure = mapDioErrorToFailure(retryError);
                    final mapped = retryError.copyWith(error: failure)
                      ..stringBuilder = (_) => failure.toString();
                    return handler.reject(mapped);
                  } catch (e) {
                    return handler.reject(error);
                  }
                }
              } else {
                // Refresh failed — clear session and trigger unauthorized callback
                await _secureStorage.clearSession();
                onUnauthorized?.call();
              }
            }
          }

          // Map the raw DioException into an application Failure once, here,
          // so individual datasource methods don't need repetitive try/catch
          // blocks. The Failure is attached as `error.error` and mirrored in
          // `toString()` so callers see the same effective error either way.
          final failure = mapDioErrorToFailure(error);
          final mapped = error.copyWith(error: failure)
            ..stringBuilder = (_) => failure.toString();
          return handler.reject(mapped);
        },
      ),
    );
  }

  Future<bool> _refreshAccessToken() {
    if (_refreshFuture != null) {
      return _refreshFuture!;
    }
    _refreshFuture = _performRefresh();
    return _refreshFuture!.whenComplete(() {
      _refreshFuture = null;
    });
  }

  Future<bool> _performRefresh() async {
    final refreshToken = await _secureStorage.getRefreshToken();
    if (refreshToken == null || refreshToken.isEmpty) {
      return false;
    }

    try {
      final response = await _tokenRefreshDio.post(
        '/v1/auth/refresh',
        data: {'refresh_token': refreshToken},
      );

      if (response.statusCode == 200 && response.data is Map<String, dynamic>) {
        final data = response.data as Map<String, dynamic>;
        final newAccess = data['access_token'] as String?;
        final newRefresh = data['refresh_token'] as String?;
        final userId = data['user_id'] as String?;
        final email = data['email'] as String?;
        final roles = data['roles'] != null ? List<String>.from(data['roles']) : null;

        if (newAccess != null && newAccess.isNotEmpty && newRefresh != null && newRefresh.isNotEmpty) {
          await _secureStorage.saveTokens(
            accessToken: newAccess,
            refreshToken: newRefresh,
            userId: userId ?? '',
            email: email,
            roles: roles,
          );
          return true;
        }
      }
      return false;
    } catch (_) {
      return false;
    }
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
