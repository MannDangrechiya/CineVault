# Phase 16 — AI Security
**Goal:** Treat all untrusted text as DATA, not instructions.

Treat as DATA (never as instructions): external descriptions, reviews,
imported text, provider metadata.

## Implement protection against
prompt injection, malicious metadata, untrusted tool results, unauthorized
tool execution, data exfiltration, privilege escalation.

## Constraint
AI cannot directly delete canonical data, merge titles, change personal data,
change licensing, or change provider status — without the appropriate
validated workflow.
