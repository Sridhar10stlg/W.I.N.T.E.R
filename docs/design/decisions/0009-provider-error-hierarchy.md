# 0009: Provider errors: a small hierarchy grouped by what the caller can do

- **Status:** Accepted
- **Date:** 2026-10-26
- **Recorded:** 2026-10-26
- **Supersedes:** the error part of [0006](0006-sync-str-return.md).

## Context and forces

- With one `ProviderError`, the caller can tell "retry" from "fix your setup" only by reading the message text. That is stringly-typed error handling: a harmless rewording silently breaks the logic, and no test notices.
- Sridhar decided a timeout should be retried once, then shown to the user. "Model not found" must never be retried. Something must tell them apart.
- Error messages are output too: they can leak secrets or untrusted data.

## Options considered

| | A. One `ProviderError` (today) | B. One type + `retryable` flag | C. Small hierarchy under `ProviderError` | D. Return `Reply` or `Failure`, no exceptions |
|---|---|---|---|---|
| **Caller can decide retry?** | Only by reading strings | Yes | Yes | Yes |
| **Breaks existing `except ProviderError`?** | n/a | No | No (subclasses still match) | Yes, every caller changes |
| **Simplicity** | Best | Very good | Good | Unusual in Python |
| **Grows later** | Poorly | More needs mean more flags | Add a subclass | Well, but costly now |

## Decision

Option C. Three subclasses of `ProviderError`, grouped by the **caller's action**, not by the technical cause:

| Type | Examples | What the caller does |
|---|---|---|
| `ProviderTemporaryError` | timeout, rate limit | A bounded retry may help |
| `ProviderUnavailableError` | Ollama not running, no network | Tell the user to start or check something |
| `ProviderSetupError` | model not found, missing or rejected key, provider not implemented | Tell the user to fix config. Never retry. |

The final names are for the code session to settle.

### Message rules for every provider error
- Say what happened, plus how to fix it (for example "Model gemma3:4b not found. Run: ollama pull gemma3:4b").
- Never include a raw response body (untrusted data).
- Never include any part of a secret, not even a prefix.
- Strip credentials from URLs before printing them.

## Why

Sridhar's "retry a timeout once, then tell the user" needs the error *type* to say whether a retry makes sense. Grouping by caller action carries exactly that decision. Subclasses keep `run_chat`'s existing `except ProviderError` working (substitutability), so the change is additive.

## Consequences and trade-offs accepted

- The factory's "not implemented" becomes a `ProviderSetupError` at startup; `main()` returns exit 2 (setup problem), not 1.
- Every adapter must map each low-level failure to one of the three types. An unmapped failure is a bug and shows a traceback (fail loud).
- Handlers must list the specific type before the general one: Python uses the first matching `except`.

## What would make us revisit this

- The retries decision puts all retrying inside the adapter, and nothing else ever branches on error type: then B is enough.
- A new failure that fits none of the three caller actions.

## Related

- ADRs: [0006](0006-sync-str-return.md), [0007](0007-cli-structure.md), [0008](0008-reply-object.md).
- plan.md: section 13 Month 1 Week 3 (clear errors for Ollama not running, model not found, timeouts), Week 4 (failure tests).

## Implementation hand-off (code session)

1. Add the three subclasses of `ProviderError` to `providers/base.py`.
2. `build_provider()` raises `ProviderSetupError`; `main()` maps it to exit 2. Update the temporary "not implemented" test.
3. Ollama adapter (Week 3): connection refused → `ProviderUnavailableError`; timeout → `ProviderTemporaryError`; model not found → `ProviderSetupError`.
4. Tests for each mapping, plus a test that no error message contains the response body or the key.
