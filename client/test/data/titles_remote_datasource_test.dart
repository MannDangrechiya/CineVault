// CineVault OS — Titles Remote Datasource Contract Unit Test (9.1)

import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:cinevault_client/core/network/api_client.dart';
import 'package:cinevault_client/data/remote/titles_remote_datasource.dart';
import 'package:dio/dio.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('TitlesRemoteDatasource Query Parameter Mismatch Tests (Phase 9.1)', () {
    late ApiClient apiClient;
    late TitlesRemoteDatasource datasource;
    late RequestOptions capturedOptions;

    setUp(() {
      FlutterSecureStorage.setMockInitialValues({});
      apiClient = ApiClient();
      apiClient.dio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            capturedOptions = options;
            return handler.resolve(
              Response(
                requestOptions: options,
                statusCode: 200,
                data: {'data': []},
              ),
            );
          },
        ),
      );
      datasource = TitlesRemoteDatasource(apiClient);
    });

    test('listTitles sends production_year and origin_country query params', () async {
      await datasource.listTitles(
        limit: 10,
        contentType: 'MOVIE',
        productionYear: 2024,
        originCountry: 'KR',
      );

      expect(capturedOptions.queryParameters['limit'], equals(10));
      expect(capturedOptions.queryParameters['content_type'], equals('MOVIE'));
      expect(capturedOptions.queryParameters['production_year'], equals(2024));
      expect(capturedOptions.queryParameters['origin_country'], equals('KR'));

      // Ensure old mis-named params are NOT present
      expect(capturedOptions.queryParameters.containsKey('year'), isFalse);
      expect(capturedOptions.queryParameters.containsKey('country'), isFalse);
    });
  });
}
