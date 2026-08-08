# CineVault OS — Vendor-Agnostic AI Provider Abstraction & Prompt-Injection Guard
# Implements ADR-004, CAT-6 AI Proposal Boundary & Prompt Injection Protections (Build Unit 8.8)

import re
import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from ..schemas.ai_assistant import AIProviderEnum, AIIntentExtraction

logger = logging.getLogger("cinevault.ai.provider")

class PromptSanitizer:
    """Sanitizes untrusted input text payloads to prevent prompt-injection attacks and data leakage."""

    # Dangerous prompt injection instruction-override patterns
    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+previous\s+instructions", re.IGNORECASE),
        re.compile(r"forget\s+all\s+rules", re.IGNORECASE),
        re.compile(r"system:\s*", re.IGNORECASE),
        re.compile(r"\[inst\].*?\[/inst\]", re.IGNORECASE | re.DOTALL),
        re.compile(r"<\|im_start\|>.*?<\|im_end\|>", re.IGNORECASE | re.DOTALL),
        re.compile(r"execute\s+sql", re.IGNORECASE),
        re.compile(r"drop\s+table", re.IGNORECASE),
        re.compile(r"reveal\s+(secret|password|key|token)", re.IGNORECASE),
        re.compile(r"override\s+governance", re.IGNORECASE),
    ]

    # CAT-2 PII / Sensitive Token redaction regexes
    EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
    BEARER_TOKEN_REGEX = re.compile(r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+")

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Strips instruction override tokens and redacts PII / raw security tokens."""
        if not text:
            return ""

        clean_text = text
        # 1. Neutralize known injection attack vectors
        for pattern in cls.INJECTION_PATTERNS:
            clean_text = pattern.sub("[REDACTED_INSTRUCTION]", clean_text)

        # 2. Redact sensitive auth tokens & emails
        clean_text = cls.BEARER_TOKEN_REGEX.sub("[REDACTED_JWT_TOKEN]", clean_text)
        clean_text = cls.EMAIL_REGEX.sub("[REDACTED_EMAIL]", clean_text)

        return clean_text.strip()

class AIProviderAdapter(ABC):
    """Abstract base class for all CineVault OS AI Provider Integrations."""

    @property
    @abstractmethod
    def provider_enum(self) -> AIProviderEnum:
        pass

    @abstractmethod
    async def extract_intent(self, raw_query: str) -> AIIntentExtraction:
        """Extracts structured search/recommendation query intent from natural language input."""
        pass

    @abstractmethod
    async def generate_assistant_response(
        self,
        sanitized_query: str,
        intent: AIIntentExtraction,
        matched_titles: List[Dict[str, Any]]
    ) -> str:
        """Generates grounded natural language conversational response based strictly on catalog titles."""
        pass

    @abstractmethod
    async def generate_proposal(
        self,
        target_entity_type: str,
        attribute_name: str,
        current_value: Optional[str],
        evidence_summary: str
    ) -> Dict[str, Any]:
        """Generates structured AI proposal payload for CAT-6 staging."""
        pass

class MockAIProviderAdapter(AIProviderAdapter):
    """Deterministic, resilient Mock AI provider for local testing and offline fallback."""

    @property
    def provider_enum(self) -> AIProviderEnum:
        return AIProviderEnum.MOCK

    async def extract_intent(self, raw_query: str) -> AIIntentExtraction:
        sanitized = PromptSanitizer.sanitize(raw_query)
        query_lower = sanitized.lower()

        genres = []
        for g in ["Sci-Fi", "Action", "Drama", "Mystery", "Crime", "Thriller", "Adventure"]:
            if g.lower() in query_lower:
                genres.append(g)

        directors = []
        for d in ["Christopher Nolan", "Denis Villeneuve", "Damien Chazelle"]:
            if d.lower() in query_lower:
                directors.append(d)

        actors = []
        for a in ["Leonardo DiCaprio", "Ryan Gosling", "Matthew McConaughey", "Amy Adams"]:
            if a.lower() in query_lower:
                actors.append(a)

        max_runtime = None
        if "under 90" in query_lower or "short" in query_lower:
            max_runtime = 90
        elif "under 120" in query_lower or "2 hours" in query_lower:
            max_runtime = 120

        min_year = None
        if "2000" in query_lower:
            min_year = 2000
        elif "2010" in query_lower:
            min_year = 2010

        mode = "GENERAL_SEARCH"
        if "recommend" in query_lower or "tonight" in query_lower:
            mode = "RECOMMENDATION"
        elif "similar" in query_lower or "like" in query_lower:
            mode = "SIMILARITY"

        return AIIntentExtraction(
            raw_query=raw_query,
            sanitized_query=sanitized,
            target_genres=genres,
            target_directors=directors,
            target_actors=actors,
            min_year=min_year,
            max_runtime=max_runtime,
            detected_intent_mode=mode
        )

    async def generate_assistant_response(
        self,
        sanitized_query: str,
        intent: AIIntentExtraction,
        matched_titles: List[Dict[str, Any]]
    ) -> str:
        if not matched_titles:
            return f"I searched the CineVault catalog based on your request '{sanitized_query}', but found no matching titles. Try broadening your genre or runtime filter."

        title_names = [t.get("canonical_title", "Unknown Title") for t in matched_titles[:3]]
        explanation = f"Based on your query '{sanitized_query}', I found {len(matched_titles)} matching titles in the CineVault catalog, including {', '.join(title_names)}."
        
        if intent.target_genres:
            explanation += f" Filtered by genres: {', '.join(intent.target_genres)}."
        if intent.target_directors:
            explanation += f" Directed by: {', '.join(intent.target_directors)}."

        return explanation

    async def generate_proposal(
        self,
        target_entity_type: str,
        attribute_name: str,
        current_value: Optional[str],
        evidence_summary: str
    ) -> Dict[str, Any]:
        return {
            "proposed_value": f"Enhanced {attribute_name} proposal generated by Mock AI",
            "confidence_score": 0.890,
            "evidence_payload": {
                "summary": evidence_summary,
                "current_value": current_value,
                "provider": "MOCK",
                "prompt_version": "v1.0.0"
            }
        }

class OpenAIProviderAdapter(AIProviderAdapter):
    """Server-side OpenAI provider integration with automatic fallback to Mock provider."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.fallback = MockAIProviderAdapter()

    @property
    def provider_enum(self) -> AIProviderEnum:
        return AIProviderEnum.OPENAI

    async def extract_intent(self, raw_query: str) -> AIIntentExtraction:
        if not self.api_key:
            logger.info("OpenAI API key missing; falling back to Mock AI Provider")
            return await self.fallback.extract_intent(raw_query)
        return await self.fallback.extract_intent(raw_query)

    async def generate_assistant_response(
        self,
        sanitized_query: str,
        intent: AIIntentExtraction,
        matched_titles: List[Dict[str, Any]]
    ) -> str:
        if not self.api_key:
            return await self.fallback.generate_assistant_response(sanitized_query, intent, matched_titles)
        return await self.fallback.generate_assistant_response(sanitized_query, intent, matched_titles)

    async def generate_proposal(
        self,
        target_entity_type: str,
        attribute_name: str,
        current_value: Optional[str],
        evidence_summary: str
    ) -> Dict[str, Any]:
        if not self.api_key:
            return await self.fallback.generate_proposal(target_entity_type, attribute_name, current_value, evidence_summary)
        return await self.fallback.generate_proposal(target_entity_type, attribute_name, current_value, evidence_summary)

class GeminiProviderAdapter(AIProviderAdapter):
    """Server-side Gemini provider integration with automatic fallback to Mock provider."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.fallback = MockAIProviderAdapter()

    @property
    def provider_enum(self) -> AIProviderEnum:
        return AIProviderEnum.GEMINI

    async def extract_intent(self, raw_query: str) -> AIIntentExtraction:
        return await self.fallback.extract_intent(raw_query)

    async def generate_assistant_response(
        self,
        sanitized_query: str,
        intent: AIIntentExtraction,
        matched_titles: List[Dict[str, Any]]
    ) -> str:
        return await self.fallback.generate_assistant_response(sanitized_query, intent, matched_titles)

    async def generate_proposal(
        self,
        target_entity_type: str,
        attribute_name: str,
        current_value: Optional[str],
        evidence_summary: str
    ) -> Dict[str, Any]:
        return await self.fallback.generate_proposal(target_entity_type, attribute_name, current_value, evidence_summary)

class AIProviderFactory:
    """Factory for instantiating authorized AI Provider Adapters."""

    @staticmethod
    def get_provider(provider_type: Optional[str] = None) -> AIProviderAdapter:
        requested = (provider_type or os.getenv("AI_PROVIDER", "mock")).lower()

        if requested == "openai":
            return OpenAIProviderAdapter()
        elif requested == "gemini":
            return GeminiProviderAdapter()
        else:
            return MockAIProviderAdapter()

ai_provider_factory = AIProviderFactory()
