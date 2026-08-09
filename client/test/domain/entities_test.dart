// CineVault OS — Domain Entities Parsing Unit Tests

import 'package:flutter_test/flutter_test.dart';
import 'package:cinevault_client/domain/entities/title.dart';
import 'package:cinevault_client/domain/entities/recommendation.dart';
import 'package:cinevault_client/domain/entities/ai_assistant.dart';

void main() {
  group('Domain Entities Serialization Tests', () {
    test('CanonicalTitleEntity parses backend TitleDetail JSON correctly', () {
      // Matches actual backend TitleDetail schema
      final json = {
        'id': '01912345-6789-7000-8000-000000000001',
        'display_id': 'MOV-000001',
        'canonical_title': 'Parasite',
        'original_title': '기생충',
        'content_type': 'MOVIE',
        'production_year': 2019,
        'synopsis': 'Greed and class discrimination threaten the newly formed symbiotic relationship.',
        'genres': ['Drama', 'Thriller'],
        'primary_edition': {
          'id': 'edition-01',
          'title_id': '01912345-6789-7000-8000-000000000001',
          'edition_name': 'Theatrical Cut',
          'runtime_minutes': 132,
          'format': 'FEATURE',
        },
        'poster_url': 'https://cdn.cinevault.org/artwork/posters/mov-000001.jpg',
      };

      final title = CanonicalTitleEntity.fromJson(json);

      expect(title.titleId, equals('01912345-6789-7000-8000-000000000001'));
      expect(title.displayId, equals('MOV-000001'));
      expect(title.primaryTitle, equals('Parasite'));
      expect(title.originalTitle, equals('기생충'));
      expect(title.releaseYear, equals(2019));
      expect(title.runtimeMinutes, equals(132));
      expect(title.overview, contains('Greed'));
      expect(title.genres, contains('Drama'));
    });

    test('CanonicalTitleEntity parses availability offers correctly', () {
      // Matches actual backend PlatformOfferSummary schema
      final json = {
        'id': '01912345-6789-7000-8000-000000000001',
        'display_id': 'MOV-000001',
        'canonical_title': 'Parasite',
        'content_type': 'MOVIE',
        'genres': [],
        'availabilities': [
          {
            'offer_id': 'offer-01',
            'platform_name': 'Watcha',
            'platform_code': 'WATCHA',
            'offer_type': 'FLATRATE',
            'country_code': 'KR',
            'valid_from': '2020-01-01T00:00:00Z',
          }
        ]
      };

      final title = CanonicalTitleEntity.fromJson(json);

      expect(title.availabilities.length, equals(1));
      expect(title.availabilities.first.platformName, equals('Watcha'));
      expect(title.availabilities.first.offerType, equals('FLATRATE'));
      expect(title.availabilities.first.offerId, equals('offer-01'));
    });

    test('RecommendationItemEntity parses grounded explanations correctly', () {
      // Matches actual backend RecommendationItemResponse schema
      final json = {
        'title_id': '01912345-6789-7000-8000-000000000002',
        'display_id': 'MOV-000002',
        'canonical_title': 'Memories of Murder',
        'content_type': 'MOVIE',
        'release_year': 2003,
        'recommendation_score': 94.0,
        'genres': ['Drama', 'Thriller'],
        'directors': ['Bong Joon-ho'],
        'is_available': true,
        'explanation': {
          'explanation_text': 'High director similarity with Bong Joon-ho works in your watch history.',
          'matched_genres': ['Drama', 'Thriller'],
          'matched_directors': ['Bong Joon-ho'],
          'matched_actors': [],
        }
      };

      final item = RecommendationItemEntity.fromJson(json);

      expect(item.titleId, equals('01912345-6789-7000-8000-000000000002'));
      expect(item.titleName, equals('Memories of Murder'));
      expect(item.recommendationScore, equals(94.0));
      expect(item.groundedExplanation.explanationText, contains('Bong Joon-ho'));
      expect(item.groundedExplanation.matchedDirectors, contains('Bong Joon-ho'));
      expect(item.groundedExplanation.matchedGenres, contains('Drama'));
    });

    test('AiResponseEntity parses backend AssistantQueryResponse correctly', () {
      // Matches actual backend AssistantQueryResponse schema
      final json = {
        'response_text': 'Here are top-rated Korean thrillers matching your taste profile.',
        'intent': {
          'raw_query': 'Recommend Korean thriller movies',
          'sanitized_query': 'Recommend Korean thriller movies',
          'detected_intent_mode': 'RECOMMENDATION',
          'target_genres': ['Thriller'],
          'target_directors': [],
          'target_actors': [],
          'preferred_content_type': 'MOVIE',
        },
        'matched_titles': [
          {'title_id': '01912345-6789-7000-8000-000000000001', 'canonical_title': 'Parasite'}
        ],
        'provider_used': 'mock',
        'is_grounded': true,
        'fallback_applied': false,
      };

      final response = AiResponseEntity.fromJson(json);

      expect(response.responseText, contains('Korean thrillers'));
      expect(response.intent.detectedIntentMode, equals('RECOMMENDATION'));
      expect(response.intent.sanitizedQuery, equals('Recommend Korean thriller movies'));
      expect(response.matchedTitles.length, equals(1));
      expect(response.isGrounded, isTrue);
      expect(response.providerUsed, equals('mock'));
    });
  });
}
