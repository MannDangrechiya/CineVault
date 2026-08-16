# Phase 12 — Recommendation Engine Foundation
**Goal:** Explainable recommendations.

## Start with
explicit preferences + curated collections + content similarity, then
progressively incorporate behavior.

## Support
content-based recommendations, genre/theme/people/franchise/country/language
similarity, runtime similarity, personal rating signals.

## Constraints
- Cold-start is mandatory: a new user gets useful recommendations with zero history.
- Every recommendation needs an explanation, e.g. "Recommended because you liked
  Parasite and prefer Korean psychological thrillers."
- Do not let an LLM decide recommendation truth directly.
