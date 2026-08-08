// CineVault OS — ApiConfig Unit Tests

import 'package:flutter_test/flutter_test.dart';
import 'package:cinevault_client/core/config/api_config.dart';

void main() {
  group('ApiConfig Unit Tests', () {
    test('baseUrl returns a non-empty string starting with http', () {
      final url = ApiConfig.baseUrl;
      expect(url, isNotEmpty);
      expect(url.startsWith('http'), isTrue);
    });

    test('Endpoint definitions match expected canonical routes', () {
      expect(ApiConfig.titlesEndpoint, equals('/v1/titles'));
      expect(ApiConfig.searchEndpoint, equals('/v1/search'));
      expect(ApiConfig.recommendationsEndpoint, equals('/v1/recommendations'));
      expect(ApiConfig.aiAssistantQueryEndpoint, equals('/v1/ai/assistant/query'));
      expect(ApiConfig.syncPushEndpoint, equals('/v1/sync/push'));
      expect(ApiConfig.syncPullEndpoint, equals('/v1/sync/pull'));
    });
  });
}
