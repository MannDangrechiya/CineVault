// CineVault OS — Domain Entities Parsing Unit Tests

import 'package:flutter_test/flutter_test.dart';
import 'package:cinevault_client/domain/entities/title.dart';
import 'package:cinevault_client/domain/entities/recommendation.dart';
import 'package:cinevault_client/domain/entities/ai_assistant.dart';

void main() {
  group('Domain Entities Serialization Tests', () {
    test('CanonicalTitleEntity parses JSON correctly', () {
      final json = {
        'title_id': '01912345-6789-7000-8000-000000000001',
        'display_id': 'MOV-000001',
        'primary_title': 'Parasite',
        'original_title': '기생충',
        'content_type': 'MOVIE',
        'release_year': 2019,
        'runtime_minutes': 132,
        'genres': ['Drama', 'Thriller'],
        'availabilities': [
          {
            'availability_id': 'avail-01',
            'platform_name': 'Hulu',
            'availability_type': 'FLATRATE',
          }
        ]
      };

      final title = CanonicalTitleEntity.fromJson(json);

      expect(title.titleId, equals('01912345-6789-7000-8000-000000000001'));
      expect(title.displayId, equals('MOV-000001'));
      expect(title.primaryTitle, equals('Parasite'));
      expect(title.originalTitle, equals('기생충'));
      expect(title.releaseYear, equals(2019));
      expect(title.genres, contains('Drama'));
      expect(title.availabilities.length, equals(1));
      expect(title.availabilities.first.platformName, equals('Hulu'));
    });

    test('RecommendationItemEntity parses grounded explanations correctly', () {
      final json = {
        'title_id': '01912345-6789-7000-8000-000000000002',
        'title_name': 'Memories of Murder',
        'recommendation_score': 0.94,
        'grounded_explanation': {
          'overall_score': 0.94,
          'content_similarity_score': 0.92,
          'taste_fit_score': 0.96,
          'popularity_score': 0.88,
          'textual_explanation': 'High director similarity with Bong Joon-ho works in your watch history.',
          'citations': ['MOV-000001'],
        }
      };

      final item = RecommendationItemEntity.fromJson(json);

      expect(item.titleId, equals('01912345-6789-7000-8000-000000000002'));
      expect(item.recommendationScore, equals(0.94));
      expect(item.groundedExplanation.tasteFitScore, equals(0.96));
      expect(item.groundedExplanation.textualExplanation, contains('Bong Joon-ho'));
      expect(item.groundedExplanation.citations, contains('MOV-000001'));
    });

    test('AiResponseEntity parses query response and citations correctly', () {
      final json = {
        'query_id': 'ai-q-100',
        'raw_query': 'Recommend Korean thriller movies',
        'response_text': 'Here are top-rated Korean thrillers matching your taste profile.',
        'detected_intent': {
          'intent_type': 'RECOMMENDATION',
          'primary_keyword': 'thriller',
          'extracted_filters': {'country': 'KR', 'genre': 'Thriller'},
        },
        'title_citations': ['01912345-6789-7000-8000-000000000001'],
        'confidence_score': 0.95,
      };

      final response = AiResponseEntity.fromJson(json);

      expect(response.queryId, equals('ai-q-100'));
      expect(response.detectedIntent.intentType, equals('RECOMMENDATION'));
      expect(response.titleCitations.length, equals(1));
      expect(response.confidenceScore, equals(0.95));
    });
  });
}
