# 0013: Streaming, turn measurement and logging

- **Status:** Accepted. Not yet implemented (code in Month 2 Week 2).
- **Date:** 2026-11-20
- **Recorded:** 2026-11-20

## Context and forces

- `generate()` returns one finished `Reply` ([ADR 0008](0008-reply-object.md)). Measured on the Dynabook: 5 to 45 seconds of silence on CPU depending on the prompt; the 4GB Dell is slower and unmeasured. Silence looks like a freeze.
- Streaming adds a failure that does not exist today: failing **halfway through an answer the user is already reading** ([ADR 0010](0010-timeouts-and-retries.md) revisit trigger, open question 4).
- Asking the model is repeatable (idempotent), but **printing is not undoable**.
- Today Ctrl+C quits the program, and the conversation lives only in memory, so quitting loses it.
- Prompts and replies are personal. Project rules: redact secrets from logs, never log complete settings, keep conversation data out of tests. Memory (Month 5) will have delete controls that a log must not defeat.
- Open questions 13 and 14, and the unverified claim in [ADR 0012](0012-conversation-ownership-and-history-limit.md) that trimming in chunks keeps turns fast, all need real numbers.
- Hard to reverse: the provider contract, and what logs are allowed to contain (personal data in log files cannot be recalled). Cheap to change: where `/stats` lives and the names of record fields.

## Options considered

### How streaming is added to the provider contract

| | A. Add `stream()`, keep a separate `generate()` per adapter | B. One method that always streams | C. A callback argument on `generate()` | D. `stream()` is the primitive; `generate()` is a thin collector in the base class |
|---|---|---|---|---|
| **Code paths per adapter** | Two (they can drift) | One | One | One |
| **Existing callers and tests** | Untouched | All change now | Untouched | Untouched |
| **Cancel and mid-answer errors** | Clear | Clear | Harder to reason about (inverted control) | Clear |
| **Grows later** (tool calls in Month 3) | OK | OK | Awkward | OK: more event types |

### A partial answer when the stream fails or is stopped

| | Keep as normal | Keep, flagged as cut off | Discard | Retry from the start |
|---|---|---|---|---|
| **Model reads a half sentence as complete** | Yes | No (flag is for the user's note; text unchanged) | n/a | n/a |
| **User can say "continue"** | Yes | Yes | No | n/a |
| **User sees the text twice** | No | No | No | Yes, and a paid API is charged twice |

### Retry for a stream

Retry always from the start (the user may watch the answer begin twice), retry only before the first piece (invisible), or never retry streams (a cold-start timeout, common on CPU, would fail more often).

### What a log line may contain

Everything; events and numbers only; events plus a short preview; everything masked by pattern. Masking by pattern recognises only known shapes (keys), not a name, an address or a diagnosis.

## Decision

1. **Option D.** `stream()` is the one primitive every adapter implements: it yields pieces of the answer and ends with the final `Reply` (shape to be fixed in the code step; Month 3 tool calls can arrive as further event types). `generate()` stays as a concrete method in the base class that collects the stream into one `Reply`. Callers that do not stream do not change; the mock streams too.
2. **A cut-off answer is kept and flagged.** If the stream fails after text arrived, or the user stops it, the partial text is stored as the assistant message and the user sees a visible note. The text sent to the model next turn is unchanged. If no text arrived, the question is crossed out as today.
3. **`RetryingProvider` retries only a failure before the first piece.** After the first piece, the failure is reported and decision 2 applies.
4. **Ctrl+C during an answer stops the answer only**: generation stops, the partial text is kept (decision 2), and the prompt returns. Ctrl+C at the prompt still quits. (Sridhar answered "quit the program"; the mentor recommended stopping the answer only, and Sridhar confirmed by approving the write-up without objecting.)
5. **One turn record per answer** (time to the first piece, total time, tokens in and out, estimated versus real size, number of dropped messages). The `/stats` command and the log both read that same record.
6. **Logs hold events and numbers only**: model name, durations, token counts, error types, timestamps, trimming counts. Never conversation text and never secrets. A redaction filter is a safety net for dynamic parts such as error messages and URLs. Logging conversation content may only ever return as an explicit, off-by-default option to a separate file (open question 17).

## Why

- **Contract grows by adding.** Changing the single method (Sridhar's first answer: "always streams") breaks every caller at once; keeping `generate()` as a collector keeps Sridhar's real worry (two code paths that can drift) solved, with one implementation per adapter and no caller changes.
- **Retry only when the failure is invisible.** Sridhar first chose "always retry from the start"; that would show the answer twice and double-charge a paid API. The two answers "keep the partial" and "retry from the start" also contradicted each other.
- **Stop sized to the thing stopped.** Quitting the program to cancel one answer throws away the whole conversation.
- **Data minimisation.** Sridhar first chose "log everything"; a log is a second copy of private conversations that outlives the chat and would defeat the Month 5 delete controls. The safest data to protect is data never stored.
- **One recorder, two readers.** Two places computing their own numbers would drift apart.

## Consequences and trade-offs accepted

- New work: `Provider.stream()` and the collector, a streaming mock, a streaming Ollama adapter with mid-stream error mapping, a `RetryingProvider` that waits for the first piece before deciding, the CLI printing pieces and handling Ctrl+C, a cut-off flag on the `Session`, a turn record and `/stats`, and a logging module with redaction.
- Tests become heavier (streaming fakes, interruption cases); logs cannot be used to reproduce a conversation bug.
- A retry after the first piece is never automatic: some failures that a retry would have hidden are now shown.
- Two Ctrl+C levels must be explained to the user.

## What would make us revisit this

- Streaming proves too costly for the deadline in Week 2 (the cut order is logging first, then OpenRouter; streaming and measurement are not cut).
- Measurements show a retry before the first piece rarely helps, or that cold starts need a different rule (open question 14).
- Debugging genuinely needs conversation content (open question 17).
- Month 3 tool calls or the OpenRouter stream format do not fit the event shape.

## Related

- ADRs: [0008](0008-reply-object.md), [0009](0009-provider-error-hierarchy.md), [0010](0010-timeouts-and-retries.md), [0012](0012-conversation-ownership-and-history-limit.md).
- Open questions: 4 (closed here), 17 (new), and the "Ollama stream format" assumption.
- plan.md: section 13 Month 2 Week 2.
- Implementation hand-off (code session), in this order:
  1. Experiment: Ollama `/api/chat` with `"stream": true`: the line format, what the last line carries (stop reason, token counts), the shape of a mid-stream failure, and time to the first piece cold and warm on `gemma3:4b`.
  2. The contract: `Provider.stream()` plus the `generate()` collector; a streaming mock; tests.
  3. The Ollama adapter streams; mid-stream error mapping; tests with `httpx.MockTransport`.
  4. `RetryingProvider`: retry only before the first piece; tests.
  5. The CLI prints pieces; Ctrl+C stops the answer; the `Session` cut-off flag and the visible note; tests.
  6. The turn record and `/stats`.
  7. Logging: events and numbers only, redaction filter, tests with canary strings (a secret in an exception message is redacted; conversation text never appears in a log).
