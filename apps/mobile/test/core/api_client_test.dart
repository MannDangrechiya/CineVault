// CineVault OS — API Client & Network Failure Unit Tests

import 'package:flutter_test/flutter_test.dart';
import 'package:cinevault_client/core/error/failures.dart';
import 'package:cinevault_client/core/network/api_client.dart';
import 'package:dio/dio.dart';

void main() {
  group('ApiClient Error Mapping Tests', () {
    late ApiClient apiClient;

    setUp(() {
      apiClient = ApiClient();
    });

    test('Maps HTTP 401 response to UnauthorizedFailure', () {
      final dioException = DioException(
        requestOptions: RequestOptions(path: '/v1/titles'),
        response: Response(
          requestOptions: RequestOptions(path: '/v1/titles'),
          statusCode: 401,
          data: {'detail': 'Invalid or expired Bearer token'},
        ),
      );

      final failure = apiClient.mapDioErrorToFailure(dioException);

      expect(failure, isA<UnauthorizedFailure>());
      expect(failure.statusCode, equals(401));
      expect(failure.message, contains('Invalid or expired Bearer token'));
    });

    test('Maps HTTP 403 response to ForbiddenFailure', () {
      final dioException = DioException(
        requestOptions: RequestOptions(path: '/internal/v1/control-room'),
        response: Response(
          requestOptions: RequestOptions(path: '/internal/v1/control-room'),
          statusCode: 403,
          data: {'detail': 'Insufficient curator privileges'},
        ),
      );

      final failure = apiClient.mapDioErrorToFailure(dioException);

      expect(failure, isA<ForbiddenFailure>());
      expect(failure.statusCode, equals(403));
      expect(failure.message, contains('Insufficient curator privileges'));
    });

    test('Maps HTTP 404 response to NotFoundFailure', () {
      final dioException = DioException(
        requestOptions: RequestOptions(path: '/v1/titles/nonexistent'),
        response: Response(
          requestOptions: RequestOptions(path: '/v1/titles/nonexistent'),
          statusCode: 404,
          data: {'detail': 'Title not found'},
        ),
      );

      final failure = apiClient.mapDioErrorToFailure(dioException);

      expect(failure, isA<NotFoundFailure>());
      expect(failure.statusCode, equals(404));
    });

    test('Maps Connection Timeout to NetworkFailure', () {
      final dioException = DioException(
        requestOptions: RequestOptions(path: '/v1/titles'),
        type: DioExceptionType.connectionTimeout,
      );

      final failure = apiClient.mapDioErrorToFailure(dioException);

      expect(failure, isA<NetworkFailure>());
    });
  });
}
