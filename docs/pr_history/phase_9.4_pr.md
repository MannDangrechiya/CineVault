## Gap Closed
> "services/api/ai/provider.py defines OpenAIProviderAdapter and GeminiProviderAdapter as stub classes that just delegate to MockAIProviderAdapter. No live HTTP call is made."

## Summary of Changes
1. **Dependencies (`requirements.txt`)**: Added `openai>=1.0.0` dependency to project requirements.
2. **Configuration (`config.py` & `.env.example`)**: Added `ai_provider`, `openai_api_key`, and `openai_model` configuration parameters and documented `AI_PROVIDER=mock|openai|gemini`.
3. **Live OpenAI Provider (`provider.py`)**: Implemented live `OpenAIProviderAdapter` using `AsyncOpenAI` SDK:
   - `extract_intent`: Uses `PromptSanitizer` + OpenAI Chat Completions JSON output format to parse query intents.
   - `generate_assistant_response`: Enforces grounded system instructions restricting responses to matched catalog titles.
   - `generate_proposal`: Generates structured proposal JSON payloads for quality staging.
   - Error handling: Raises explicit exceptions when API key is missing or calls fail under `AI_PROVIDER=openai` (no silent mock fallback).
4. **Unit & Safety Tests (`test_openai_provider.py`)**: Added test suite covering prompt injection sanitization, intent extraction, grounded responses, proposal payload structure, and fail-loud error paths using `AsyncOpenAI` mocks.

## Test Evidence
- **Backend Test (`python -m pytest -v`)**: 134 passed, 0 failures (100% pass rate).
- **Flutter Analysis (`flutter analyze`)**: No issues found!
- **Flutter Test (`flutter test`)**: 17 passed, 0 failures.

## Follow-up / Next Phases
- Phase 9.5: Implement live Gemini provider adapter.
