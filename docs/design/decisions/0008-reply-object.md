# 0008: Provider returns a `Reply` object (text, stop reason, usage)

- **Status:** Accepted
- **Date:** 2026-10-26
- **Recorded:** 2026-10-26
- **Supersedes:** the return-type part of [0006](0006-sync-str-return.md). The synchronous call and the single `ProviderError` remain under 0006 for now.

## Context and forces

- `generate() -> str` throws away information the adapter already receives: the stop reason (was the reply cut off?) and token usage (needed for Month 2 cost tracking).
- Month 3 adds tool calls proposed by the model.
- The contract is still cheap to change: no real adapter exists yet. After Block 3 (Ollama adapter) it becomes expensive, because every adapter, the mock, the CLI and the tests depend on it.

## Options considered

| | A. Keep `str` | B. `Reply(text)` only | C. `Reply(text, stop_reason, usage)` | D. Streaming now |
|---|---|---|---|---|
| **How** | Today's code | Result object, one field | Result object; extra fields optional (`None`) | `generate()` yields chunks |
| **Simplicity** | Best | Very good | Good | Worst |
| **Testability** | Best | Very good | Good (mock leaves fields `None`) | Hardest |
| **Safety** | Cut-off replies invisible | Same as A | Cut-off replies detectable | Errors mid-reply |
| **Cost tracking (Month 2)** | Needs a type change | Needs a field | Ready | Needs extra design |
| **Effort now** | 0 | ~1 hour | ~1-2 hours | Days |
| **Reversibility** | Gets worse each week | Good | Good | Poor |

- **A** makes the Month 2 and Month 3 changes break every adapter at once.
- **B** keeps the door open but throws away data Ollama already returns in Week 3.
- **D** is not needed now: streaming can be added later as a separate `stream()` method, which is an addition and breaks nothing.

## Decision

Option C. `generate(messages) -> Reply`. `Reply` is a frozen object with:
- `text` (required),
- `stop_reason` (optional, default `None`),
- `usage` (optional, default `None`): input and output token counts.

No tool calls yet. The call stays synchronous.

## Why

Sridhar: decide before Week 3, so the first real adapter is built on the right contract.

The principle: decide the *shape* now, and fill it only with what Week 3 naturally provides. You cannot build it "correct the first time"; aim to make the next change cheap. Adding a field later breaks nothing; changing a type breaks everything.

## Consequences and trade-offs accepted

- A small one-off change to the mock, `run_chat` and the tests.
- A cut-off reply becomes detectable.
- Usage data is ready for Month 2 cost tracking.
- Adapters must translate vendor field names (for example Ollama's or OpenRouter's) into W.I.N.T.E.R's own `stop_reason` and `usage`. Vendor names never leave the adapter (anti-corruption layer).
- `Reply.text` is model output and stays **untrusted** (see [trust boundaries](../diagrams/trust-boundaries.md)).

## What would make us revisit this

- Ollama does not reliably return the stop reason or token counts: fall back to `Reply(text)` with the other fields left `None`.
- Month 2 Week 2 (streaming): add a separate `stream()` method.
- Month 3 (tool calls): add `tool_calls` to `Reply` and a `"tool"` role to `Message`.

## Related

- ADRs: [0005](0005-provider-abc.md), [0006](0006-sync-str-return.md), [0007](0007-cli-structure.md).
- plan.md: section 13 Month 1 Week 3, Month 2 Week 2, Month 3.

## Implementation hand-off (code session)

1. Add `Reply` and `Usage` (frozen dataclasses) to `providers/base.py`.
2. `Provider.generate()` returns `Reply`; `MockProvider` returns `Reply(text=...)`.
3. `run_chat` uses `reply.text` when printing and storing the assistant message.
4. Update the provider and CLI tests.
5. Ollama adapter: map its stop-reason and token-count fields into `Reply`. Verify the real field names against Ollama v0.40.11 output first.
6. Optional: the CLI prints a short note when `stop_reason` says the reply was cut off.
