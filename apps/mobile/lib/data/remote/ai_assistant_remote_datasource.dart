// CineVault OS — AI Assistant Remote Datasource (8.8)

import '../../core/config/api_config.dart';
import '../../core/network/api_client.dart';
import '../../domain/entities/ai_assistant.dart';

class AiAssistantRemoteDatasource {
  final ApiClient _apiClient;

  AiAssistantRemoteDatasource(this._apiClient);

  Future<AiResponseEntity> processQuery(String queryText) async {
    final payload = {
      'query_text': queryText,
    };

    final response = await _apiClient.dio.post(
      ApiConfig.aiAssistantQueryEndpoint,
      data: payload,
    );

    return AiResponseEntity.fromJson(response.data);
  }

  Future<AiIntentEntity> extractIntent(String queryText) async {
    final response = await _apiClient.dio.post(
      ApiConfig.aiAssistantIntentEndpoint,
      queryParameters: {'query_text': queryText},
    );

    return AiIntentEntity.fromJson(response.data);
  }
}
