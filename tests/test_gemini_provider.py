# CineVault OS — Gemini Provider Integration & Safety Unit Tests (Phase 9.5)

import pytest
import unittest
from unittest.mock import AsyncMock, MagicMock
from services.api.ai.provider import (
    GeminiProviderAdapter,
    AIProviderFactory,
)
from services.api.schemas.ai_assistant import AIProviderEnum, AIIntentExtraction


class TestGeminiProviderAdapter(unittest.IsolatedAsyncioTestCase):

    async def test_gemini_provider_missing_key_falls_back(self):
        adapter = GeminiProviderAdapter(api_key=None)
        adapter.client = None

        intent = await adapter.extract_intent("sci-fi movies under 90 minutes")
        self.assertIn("Sci-Fi", intent.target_genres)
        self.assertEqual(intent.max_runtime, 90)

    async def test_gemini_extract_intent_mocked(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"target_genres": ["Sci-Fi"], "target_directors": ["Denis Villeneuve"], "min_year": 2021, "detected_intent_mode": "RECOMMENDATION"}'
        mock_client.models.generate_content = MagicMock(return_value=mock_response)

        adapter = GeminiProviderAdapter(api_key="mock-gemini-key", client=mock_client)
        intent = await adapter.extract_intent("Denis Villeneuve sci-fi movies 2021")

        self.assertEqual(intent.target_genres, ["Sci-Fi"])
        self.assertEqual(intent.target_directors, ["Denis Villeneuve"])
        self.assertEqual(intent.min_year, 2021)
        self.assertEqual(intent.detected_intent_mode, "RECOMMENDATION")
        self.assertEqual(adapter.provider_enum, AIProviderEnum.GEMINI)

    async def test_gemini_generate_assistant_response_mocked(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Based on catalog data, Dune: Part One matches your request."
        mock_client.models.generate_content = MagicMock(return_value=mock_response)

        adapter = GeminiProviderAdapter(api_key="mock-gemini-key", client=mock_client)
        intent = AIIntentExtraction(
            raw_query="dune movies",
            sanitized_query="dune movies",
            detected_intent_mode="RECOMMENDATION"
        )
        matched_titles = [{"canonical_title": "Dune: Part One"}]

        resp = await adapter.generate_assistant_response("dune movies", intent, matched_titles)
        self.assertIn("Dune: Part One", resp)

    async def test_gemini_generate_proposal_mocked(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"proposed_value": "Enhanced Synopsis Proposal", "confidence_score": 0.92, "reasoning": "Grounded evidence"}'
        mock_client.models.generate_content = MagicMock(return_value=mock_response)

        adapter = GeminiProviderAdapter(api_key="mock-gemini-key", client=mock_client)
        proposal = await adapter.generate_proposal(
            target_entity_type="TITLE",
            attribute_name="synopsis",
            current_value="Old value",
            evidence_summary="Verified evidence"
        )

        self.assertEqual(proposal["proposed_value"], "Enhanced Synopsis Proposal")
        self.assertEqual(proposal["confidence_score"], 0.92)
        self.assertEqual(proposal["evidence_payload"]["provider"], "GEMINI")

    async def test_gemini_api_error_raises_runtime_error(self):
        mock_client = MagicMock()
        mock_client.models.generate_content = MagicMock(side_effect=Exception("Gemini API Error"))

        adapter = GeminiProviderAdapter(api_key="mock-gemini-key", client=mock_client)
        with self.assertRaises(RuntimeError) as ctx:
            await adapter.extract_intent("sci-fi movies")
        self.assertIn("Gemini AI Provider error", str(ctx.exception))


class TestAIProviderFactoryGemini(unittest.TestCase):

    def test_factory_returns_gemini_when_requested(self):
        provider = AIProviderFactory.get_provider("gemini")
        self.assertEqual(provider.provider_enum, AIProviderEnum.GEMINI)


if __name__ == "__main__":
    unittest.main()
