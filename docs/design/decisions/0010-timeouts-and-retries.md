# 0010: Timeouts and retries: one wrapper layer, never retry actions

- **Status:** Accepted
- **Date:** 2026-10-26
- **Recorded:** 2026-10-26

## Context and forces

- Calls to Ollama or OpenRouter can hang. Without a timeout the app freezes and has no stop path.
- A cold 1B model on the 4GB Dell often times out on the first call; one retry usually fixes it.
- If several layers retry, attempts multiply (3 tries × 3 tries = 9 calls for one question).
- From Month 3, tools can change things outside the app. A timeout on an action does not mean it failed.

## Options considered

- **Retry inside each adapter:** works, but every adapter repeats the same logic.
- **Retry in `run_chat`:** mixes reliability logic into the interface; voice would need it again.
- **A `RetryingProvider` wrapper (chosen):** wraps any provider, same interface; one place for the rule.
- **Retry in several layers:** rejected; causes retry amplification.

## Decision

1. Every provider call has a timeout. The number of seconds comes from `Settings`, so each laptop can set its own.
2. Retries happen in **one layer only**: a `RetryingProvider` that retries `ProviderTemporaryError` **once**, then lets the error reach the user. Adapters and the CLI never retry.
3. `ProviderSetupError` and `ProviderUnavailableError` are never retried.
4. **Actions are never retried automatically** (Month 3 onward). A timed-out action is reported to the user, who decides. Only safe-to-repeat (idempotent) calls such as asking the model may be retried.

## Why

Sridhar chose the wrapper so the rule lives in one place. One layer avoids amplification. Rule 4 prevents duplicate side effects, such as sending a message twice.

## Consequences and trade-offs accepted

- A retry on a paid API costs money; one retry keeps that bounded.
- The wrapper depends on the error types from [0009](0009-provider-error-hierarchy.md).
- A slow laptop needs a larger timeout in `.env`.

## What would make us revisit this

- Retries prove too few or too many in real use (measure in Month 2).
- Streaming (Month 2): a failure halfway through a reply cannot simply be retried.

## Related

- ADRs: [0008](0008-reply-object.md), [0009](0009-provider-error-hierarchy.md).
- plan.md: section 13 Month 1 Week 3 (timeouts), Month 3 (tools and confirmation).

## Implementation hand-off (code session)

1. Add a validated timeout setting (seconds, positive) to `Settings` and `.env.example`.
2. Adapters pass the timeout to their HTTP call and raise `ProviderTemporaryError` when it expires.
3. Add `RetryingProvider(inner)`: retries `ProviderTemporaryError` once; nothing else.
4. Tests: retries once and then raises; does not retry setup or unavailable errors; returns the reply on a successful retry.
