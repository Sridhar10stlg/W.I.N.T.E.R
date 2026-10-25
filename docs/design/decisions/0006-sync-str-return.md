# 0006: Provider contract: synchronous `generate(list[Message]) -> str` and one `ProviderError`

- **Status:** Accepted (retroactive). **Return type superseded by [0008](0008-reply-object.md)** (`generate()` now returns a `Reply`). **Error part superseded by [0009](0009-provider-error-hierarchy.md)** (small hierarchy under `ProviderError`). The synchronous call remains in force.
- **Date:** 2026-10-26 (introduced in commit `4ee37b4`)
- **Recorded:** 2026-10-26

## Context and forces

- This is the most important contract in W.I.N.T.E.R today. The CLI, the mock, about 16 tests, every future adapter, and later the orchestrator, voice and memory all depend on it.
- It is cheap to change now (no real adapter exists yet) and gets more expensive with every adapter and test built on it.
- Coming soon in plan.md: streaming and cost/latency measurement (Month 2 Week 2), tool calls proposed by the model (Months 2-3), audit log (Month 3).
- A 1B model on the 4GB Dell can be slow; a reply that appears only when complete may feel frozen.

## Options considered

### Option A: synchronous, returns the full reply as `str` (chosen)
- **Pros:** simplest possible contract; trivial to mock and test; the CLI loop stays very short.
- **Cons:** nowhere to return token usage, why the model stopped, or tool calls. The adapter receives that information and must throw it away.
- **Makes hard later:** cost measurement and tool calling both require changing the type, which touches every adapter, the mock, the CLI and tests.

### Option B: synchronous, returns a small result object (for example `Reply(text, ...)`)
- **Pros:** grows by adding fields, without breaking consumers.
- **Cons:** slightly more code today for fields not yet used.
- **Makes hard later:** nothing obvious.

### Option C: streaming (yields pieces of text as they arrive)
- **Pros:** the user sees words immediately; matters on slow laptops.
- **Cons:** more complex to test and to handle errors mid-stream.
- **Makes hard later:** nothing, but it is planned for Month 2, not Month 1.

### Option D: async (`async def generate`)
- **Pros:** fits voice and web interfaces that handle several things at once.
- **Cons:** spreads `async` through the whole call chain; harder to learn and test.
- **Makes hard later:** nothing now, but switching later is invasive.

### Error contract (same decision)
- **One `ProviderError` (chosen):** each adapter translates its own failures; the CLI catches one type.
- **A hierarchy** (for example unavailable, auth, rate limit, timeout): the caller can react differently (retry vs. tell the user).
- Note: `build_provider()` also raises `ProviderError` for "not implemented", which is a configuration problem rather than a model failure.

## Decision

`Provider.generate(messages: list[Message]) -> str`, synchronous. Any failure raises `ProviderError` with a friendly message.

## Why

From the Block 2 page: "One method keeps adapters swappable" and "The CLI handles one error type; each adapter translates its own failures."

## Consequences and trade-offs accepted

- Usage, timing, stop reason and tool calls cannot cross the boundary yet.
- The CLI cannot tell a retryable failure from a fatal one without reading the message text.
- Where timeouts and retries live is not yet decided.

## What would make us revisit this

- **Now:** before the Ollama adapter (Month 1 Week 3) is written against it. This is mentoring topic 1.
- Month 2 Week 2: streaming and cost measurement.
- Month 3: tool calls.

## Related

- ADRs: [0005](0005-provider-abc.md), [0007](0007-cli-structure.md).
- plan.md: section 13 Month 1 Week 3, Month 2, Month 3.
- Build page: [20261026_block2.md](../../Build/20261026_block2.md).
