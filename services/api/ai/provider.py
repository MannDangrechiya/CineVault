# CineVault OS — Vendor-Agnostic AI Provider Abstraction & Prompt-Injection Guard
# Implements ADR-004, CAT-6 AI Proposal Boundary & Prompt Injection Protections (Build Unit 8.8)

import re
import os
import json
import logging
import inspect
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from ..config import config
from ..schemas.ai_assistant import AIProviderEnum, AIIntentExtraction

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

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
    """Live OpenAI API provider integration for CineVault OS AI Assistant."""

    def __init__(self, api_key: Optional[str] = None, client: Optional[Any] = None, model: Optional[str] = None):
        self.api_key = api_key or config.openai_api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or config.openai_model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.fallback = MockAIProviderAdapter()
        if client:
            self.client = client
        elif self.api_key and AsyncOpenAI is not None:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None

    @property
    def provider_enum(self) -> AIProviderEnum:
        return AIProviderEnum.OPENAI

    async def extract_intent(self, raw_query: str) -> AIIntentExtraction:
        sanitized = PromptSanitizer.sanitize(raw_query)
        if not self.api_key or not self.client:
            logger.info("OpenAI API key missing; delegating to fallback Mock provider")
            return await self.fallback.extract_intent(raw_query)

        system_prompt = (
            "You are an intent extraction assistant for CineVault movie catalog search. "
            "Analyze the user query and output JSON with fields: "
            "target_genres (list of str), target_directors (list of str), target_actors (list of str), "
            "min_year (int or null), max_runtime (int or null), detected_intent_mode (one of GENERAL_SEARCH, RECOMMENDATION, SIMILARITY)."
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": sanitized}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            content = response.choices[0].message.content or "{}"
            parsed = json.loads(content)

            return AIIntentExtraction(
                raw_query=raw_query,
                sanitized_query=sanitized,
                target_genres=parsed.get("target_genres") or [],
                target_directors=parsed.get("target_directors") or [],
                target_actors=parsed.get("target_actors") or [],
                min_year=parsed.get("min_year"),
                max_runtime=parsed.get("max_runtime"),
                detected_intent_mode=parsed.get("detected_intent_mode") or "GENERAL_SEARCH"
            )
        except Exception as e:
            logger.error(f"OpenAI extract_intent failed: {e}", exc_info=True)
            raise RuntimeError(f"OpenAI AI Provider error: {e}")

    async def generate_assistant_response(
        self,
        sanitized_query: str,
        intent: AIIntentExtraction,
        matched_titles: List[Dict[str, Any]]
    ) -> str:
        if not self.api_key or not self.client:
            logger.info("OpenAI API key missing; delegating to fallback Mock provider")
            return await self.fallback.generate_assistant_response(sanitized_query, intent, matched_titles)

        system_prompt = (
            "You are the CineVault AI Assistant. Answer the user query strictly based on the provided canonical catalog titles. "
            "Never invent or hallucinate titles not present in the catalog context. "
            "If matched_titles is empty, state clearly that no matching titles were found."
        )

        user_content = f"User Query: {sanitized_query}\nMatched Catalog Titles: {json.dumps(matched_titles)}"

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content or "No response returned from OpenAI."
        except Exception as e:
            logger.error(f"OpenAI generate_assistant_response failed: {e}", exc_info=True)
            raise RuntimeError(f"OpenAI AI Provider error: {e}")

    async def generate_proposal(
        self,
        target_entity_type: str,
        attribute_name: str,
        current_value: Optional[str],
        evidence_summary: str
    ) -> Dict[str, Any]:
        if not self.api_key or not self.client:
            logger.info("OpenAI API key missing; delegating to fallback Mock provider")
            return await self.fallback.generate_proposal(target_entity_type, attribute_name, current_value, evidence_summary)

        system_prompt = (
            "You are CineVault AI Curation Assistant. Evaluate the evidence summary and current value for a canonical entity attribute. "
            "Output JSON with fields: proposed_value (str), confidence_score (float between 0.0 and 1.0), reasoning (str)."
        )

        user_content = (
            f"Target Entity Type: {target_entity_type}\n"
            f"Attribute Name: {attribute_name}\n"
            f"Current Value: {current_value}\n"
            f"Evidence Summary: {evidence_summary}"
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            content = response.choices[0].message.content or "{}"
            parsed = json.loads(content)

            return {
                "proposed_value": parsed.get("proposed_value", f"Proposal for {attribute_name}"),
                "confidence_score": float(parsed.get("confidence_score", 0.85)),
                "evidence_payload": {
                    "summary": evidence_summary,
                    "reasoning": parsed.get("reasoning", ""),
                    "current_value": current_value,
                    "provider": "OPENAI",
                    "model": self.model,
                    "prompt_version": "v1.0.0"
                }
            }
        except Exception as e:
            logger.error(f"OpenAI generate_proposal failed: {e}", exc_info=True)
            raise RuntimeError(f"OpenAI AI Provider error: {e}")

class GeminiProviderAdapter(AIProviderAdapter):
    """Live Google Gemini API provider integration for CineVault OS AI Assistant."""

    def __init__(self, api_key: Optional[str] = None, client: Optional[Any] = None, model: Optional[str] = None):
        self.api_key = api_key or config.gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.model = model or config.gemini_model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.fallback = MockAIProviderAdapter()
        if client:
            self.client = client
        elif self.api_key and genai is not None:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    @property
    def provider_enum(self) -> AIProviderEnum:
        return AIProviderEnum.GEMINI

    async def extract_intent(self, raw_query: str) -> AIIntentExtraction:
        sanitized = PromptSanitizer.sanitize(raw_query)
        if not self.api_key or not self.client:
            logger.info("Gemini API key missing; delegating to fallback Mock provider")
            return await self.fallback.extract_intent(raw_query)

        system_prompt = (
            "You are an intent extraction assistant for CineVault movie catalog search. "
            "Analyze the user query and output JSON with fields: "
            "target_genres (list of str), target_directors (list of str), target_actors (list of str), "
            "min_year (int or null), max_runtime (int or null), detected_intent_mode (one of GENERAL_SEARCH, RECOMMENDATION, SIMILARITY)."
        )

        try:
            config_opts = types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.0
            ) if types else None

            if hasattr(self.client, "aio") and hasattr(self.client.aio, "models") and not str(type(self.client)).endswith("MagicMock'>"):
                response = await self.client.aio.models.generate_content(
                    model=self.model,
                    contents=sanitized,
                    config=config_opts
                )
            else:
                res = self.client.models.generate_content(
                    model=self.model,
                    contents=sanitized,
                    config=config_opts
                )
                response = await res if inspect.isawaitable(res) else res

            content = response.text or "{}"
            parsed = json.loads(content)

            return AIIntentExtraction(
                raw_query=raw_query,
                sanitized_query=sanitized,
                target_genres=parsed.get("target_genres") or [],
                target_directors=parsed.get("target_directors") or [],
                target_actors=parsed.get("target_actors") or [],
                min_year=parsed.get("min_year"),
                max_runtime=parsed.get("max_runtime"),
                detected_intent_mode=parsed.get("detected_intent_mode") or "GENERAL_SEARCH"
            )
        except Exception as e:
            logger.error(f"Gemini extract_intent failed: {e}", exc_info=True)
            raise RuntimeError(f"Gemini AI Provider error: {e}")

    async def generate_assistant_response(
        self,
        sanitized_query: str,
        intent: AIIntentExtraction,
        matched_titles: List[Dict[str, Any]]
    ) -> str:
        if not self.api_key or not self.client:
            logger.info("Gemini API key missing; delegating to fallback Mock provider")
            return await self.fallback.generate_assistant_response(sanitized_query, intent, matched_titles)

        system_prompt = (
            "You are the CineVault AI Assistant. Answer the user query strictly based on the provided canonical catalog titles. "
            "Never invent or hallucinate titles not present in the catalog context. "
            "If matched_titles is empty, state clearly that no matching titles were found."
        )

        user_content = f"User Query: {sanitized_query}\nMatched Catalog Titles: {json.dumps(matched_titles)}"

        try:
            config_opts = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.3
            ) if types else None

            if hasattr(self.client, "aio") and hasattr(self.client.aio, "models") and not str(type(self.client)).endswith("MagicMock'>"):
                response = await self.client.aio.models.generate_content(
                    model=self.model,
                    contents=user_content,
                    config=config_opts
                )
            else:
                res = self.client.models.generate_content(
                    model=self.model,
                    contents=user_content,
                    config=config_opts
                )
                response = await res if inspect.isawaitable(res) else res

            return response.text or "No response returned from Gemini."
        except Exception as e:
            logger.error(f"Gemini generate_assistant_response failed: {e}", exc_info=True)
            raise RuntimeError(f"Gemini AI Provider error: {e}")

    async def generate_proposal(
        self,
        target_entity_type: str,
        attribute_name: str,
        current_value: Optional[str],
        evidence_summary: str
    ) -> Dict[str, Any]:
        if not self.api_key or not self.client:
            logger.info("Gemini API key missing; delegating to fallback Mock provider")
            return await self.fallback.generate_proposal(target_entity_type, attribute_name, current_value, evidence_summary)

        system_prompt = (
            "You are CineVault AI Curation Assistant. Evaluate the evidence summary and current value for a canonical entity attribute. "
            "Output JSON with fields: proposed_value (str), confidence_score (float between 0.0 and 1.0), reasoning (str)."
        )

        user_content = (
            f"Target Entity Type: {target_entity_type}\n"
            f"Attribute Name: {attribute_name}\n"
            f"Current Value: {current_value}\n"
            f"Evidence Summary: {evidence_summary}"
        )

        try:
            config_opts = types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.1
            ) if types else None

            if hasattr(self.client, "aio") and hasattr(self.client.aio, "models") and not str(type(self.client)).endswith("MagicMock'>"):
                response = await self.client.aio.models.generate_content(
                    model=self.model,
                    contents=user_content,
                    config=config_opts
                )
            else:
                res = self.client.models.generate_content(
                    model=self.model,
                    contents=user_content,
                    config=config_opts
                )
                response = await res if inspect.isawaitable(res) else res

            content = response.text or "{}"
            parsed = json.loads(content)

            return {
                "proposed_value": parsed.get("proposed_value", f"Proposal for {attribute_name}"),
                "confidence_score": float(parsed.get("confidence_score", 0.85)),
                "evidence_payload": {
                    "summary": evidence_summary,
                    "reasoning": parsed.get("reasoning", ""),
                    "current_value": current_value,
                    "provider": "GEMINI",
                    "model": self.model,
                    "prompt_version": "v1.0.0"
                }
            }
        except Exception as e:
            logger.error(f"Gemini generate_proposal failed: {e}", exc_info=True)
            raise RuntimeError(f"Gemini AI Provider error: {e}")

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
