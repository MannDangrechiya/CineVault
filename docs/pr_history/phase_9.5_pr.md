## Gap Closed
> "services/api/ai/provider.py GeminiProviderAdapter stub class delegates to MockAIProviderAdapter. No live HTTP call is made."

## Summary of Changes
1. **Dependencies (`requirements.txt`)**: Added `google-genai>=2.0.0` dependency.
2. **Configuration (`config.py` & `.env.example`)**: Added `gemini_api_key` and `gemini_model` configuration parameters and documented `GEMINI_API_KEY` in `.env.example`.
3. **Live Gemini Provider (`provider.py`)**: Implemented live `GeminiProviderAdapter` using `google-genai` SDK (`genai.Client`):
   - `extract_intent`: Uses `PromptSanitizer` + Gemini JSON mode to parse query intents.
   - `generate_assistant_response`: Enforces grounded system instructions restricting responses to matched catalog titles.
   - `generate_proposal`: Generates structured proposal JSON payloads for quality staging.
   - Error handling: Raises explicit exceptions when API calls fail under `AI_PROVIDER=gemini`, and falls back to `MockAIProviderAdapter` when unconfigured.
4. **Unit & Safety Tests (`test_gemini_provider.py`)**: Added test suite covering intent extraction, prompt sanitization, grounded responses, proposal payload structure, and error paths using `genai.Client` mocks.

## Test Evidence
- **Backend Test (`python -m pytest -v`)**: 142 passed, 0 failures (100% pass rate).
- **Flutter Analysis (`flutter analyze`)**: No issues found!
- **Flutter Test (`flutter test`)**: 17 passed, 0 failures.

## Follow-up / Next Phases
- Phase 9.6: Implement live KOBIS + TVDB ingestion adapters.
