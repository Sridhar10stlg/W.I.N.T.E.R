# 0012: Conversation ownership and the history limit

- **Status:** Accepted. **Implemented** 2026-11-20 in Month 2 Week 1 (`8d7bef2`, `f1f67d8`, `fd0f29e`, `3f5f6ae`, `7c3ba5e`, `9140e3f`, `8ac11e5`, `b1b4143`, `fe9e804`); see the [build page](../../Build/20261120_month2_week1.md). Refinement 4 (the safety net) is deliberately not built.
- **Date:** 2026-11-20
- **Recorded:** 2026-11-20

## Context and forces

- Today `run_chat` owns the history as a local list ([ADR 0007](0007-cli-structure.md)), and there is no system prompt.
- More interfaces and features will need the same conversation behaviour: voice (Month 4), maybe a web page, tool results (Month 3), remembered facts (Month 5).
- Measured on 2026-11-19: Ollama's default context window is 4096 tokens for `gemma3:4b` (the model itself supports 131072). Believed, not verified: older messages may be dropped silently when a chat grows past it ([open question 12](../open-questions.md)).
- Silent forgetting is a trust failure: the assistant keeps answering confidently while missing what the user said earlier.
- Model output, web pages and user text are untrusted. They must never change the assistant's standing rules.
- Hard to reverse: **who owns the conversation**, and **what shape the history may have**. Cheap to change: how size is estimated, and how the system prompt is stored.

## Options considered

### Who owns the conversation

| | A. Each interface keeps its own list | B. A small session object | C. A full orchestrator |
|---|---|---|---|
| **Today's cost** | Lowest | Low (one small class) | High; more than we need |
| **When voice arrives** | Every rule copied, then drifting apart | Voice uses the same object | Works |
| **Fixing a trimming bug** | Once per interface | Once | Once |
| **Risk** | Duplication | Almost none | Building tool coordination before tools exist |

### What happens when a chat outgrows the window

| | Drop silently | Drop and tell the user | Stop and ask for a new chat | Summarise old messages |
|---|---|---|---|---|
| **User sees a problem?** | No (the trust failure) | Yes, visibly | Yes | Not unless it goes wrong |
| **Extra cost** | None | None | None | One more model call per trim (seconds on CPU) |
| **Risk** | Silent forgetting | Low | Interrupts the user | A small model can distort facts; the summary is untrusted model output and can carry a bad message forward |
| **Needs first** | n/a | Size measurement | Size measurement | Size measurement and the trimming logic |

## Decision

1. **Option B for ownership.** A small session object owns the messages and the system prompt. Interfaces use it. A future orchestrator would use the session object too.
2. **Drop and tell, for version 1.** When the conversation is too big, drop the oldest whole exchanges and show the user a visible note. Summarising is a planned upgrade (open question 15), not part of this block.
3. **Trimming rules.** The history is always whole question-and-answer pairs (an invariant). Priority when space is short:
   1. the system prompt;
   2. the newest user message;
   3. the first message, only if it fits;
   4. the most recent exchanges;
   5. everything else, dropped oldest first, in whole pairs.

   If priorities 1 and 2 alone do not fit, the user's message is too long: say so visibly and send nothing.

Smaller decisions recorded alongside (cheap to change, so no separate ADR):

- **System prompt** is a plain text file in the repo (for example `prompts/system.txt`), read at startup. A blank is filled with the standard library's `string.Template`, only with values we supply. It changes only by editing the file: not by a chat command, and never by model output. Jinja2 waits until a prompt needs logic (open question 16).
- **Size** is a character estimate (about 4 characters per token) with a safety margin, calibrated against the real token counts in `Reply.usage`.
- **Window setting:** a new `LOCAL_AI_CONTEXT_TOKENS` (default 4096) drives our budget, and the Ollama adapter sends the same number as `num_ctx`, so our budget and the server's window cannot disagree. (`/api/chat` honors `options.num_ctx`: verified by experiment (a), see the update section below.)
- **Measure before building:** first run an experiment to see what Ollama really does past 4096 tokens.

## Why

- **Single source of truth.** A rule that must behave the same everywhere lives in one place, the same reason `RetryingProvider` exists. Sridhar first chose "each interface" for simplicity; after the voice example (a trimming bug fixed once per interface) the session object was chosen as the cheaper design overall.
- **Fail loud, build simple first.** Visible dropping fixes the real problem (silent forgetting) with almost no risk. Summarising is more powerful but adds cost, latency, a distortion risk and an untrusted-output risk, and it needs the trimming logic anyway. Sridhar's choice of summarising stays on the roadmap as the upgrade.
- **Invariants.** Whole pairs only, because a reply without its question is an invalid conversation (some providers reject it). Sridhar's three protected items (system prompt, newest message, first message) are in the priority list; "whole exchanges" and the priority order were added in the review.
- **Trust boundary.** The rules file is changed only by the maintainer, through git review. Conversation text is added as messages and never rendered into a template.

## Consequences and trade-offs accepted

- New work: a session class, `Settings.context_tokens`, an `num_ctx` option in the Ollama adapter, a system prompt file and its loader, a visible "forgot early messages" note, and tests for each trimming rule.
- The character estimate is approximate. The safety margin means the assistant forgets slightly earlier than strictly needed.
- Dropped messages are gone until summarising or Month 5 memory exists.
- A larger window means more RAM and slower answers on the CPU, so the default stays 4096.
- `run_chat` changes: it stops owning the list and asks the session instead.

## What would make us revisit this

- The experiment shows Ollama behaves differently from what we believe (for example it errors instead of dropping).
- Estimated and real token counts differ by more than the safety margin in the Month 2 Week 2 measurements.
- Month 3 tools need coordination that does not fit a session object: introduce the orchestrator then, on top of the session.
- A second conversation at once (web users) makes one global session wrong.
- Summarising becomes affordable after the Month 2 Week 2 cost and latency data.

## Update after experiment (a), 2026-11-20

Measured on the Dynabook (`gemma3:1b`, Ollama 0.40.11, CPU only): a first message hides a code word, 110 filler exchanges follow, then the question.

| Round | Tokens Ollama read | Result |
|---|---|---|
| Short chat (control) | 56 | Code word recalled. |
| Long chat, default window | 4,057 of 7,426 sent | **Code word forgotten; answer confidently wrong; HTTP 200, `done_reason: stop`, no warning.** |
| Long chat, `num_ctx: 8192` | 7,426 | Code word recalled; `ollama ps` shows CONTEXT 8192. |

Confirmed facts:

- **Silent truncation is real.** About 45% of the chat was dropped from the front, with nothing in the response to say so. This is the failure this ADR exists to prevent.
- **`options.num_ctx` is honored.** The decision to send our budget as `num_ctx` stands.
- **The 4-characters-per-token estimate is too optimistic.** 27,640 characters came to 7,426 real tokens (3.7 characters per token, including per-message overhead). The estimate said 6,910, an undercount of about 7%: the dangerous direction, because we would believe a chat fits when it does not.
- **Cost grows with history.** Reading 4,057 tokens took about 22 s; 7,426 tokens about 45 s (including reloading the model at the new window), on the 1b model. The 4b model will be slower.

Refinements to the decisions above (confirmed by Sridhar 2026-11-20; number 4 is only recorded for later, not part of Month 2 Week 1 unless the estimate proves unreliable):

1. **Estimate with 3 characters per token** (it overestimates on purpose), instead of 4. Re-check against `Reply.usage` in Month 2 Week 2.
2. **Reserve room for the reply.** The window holds the prompt and the answer, so the prompt budget is `context_tokens` minus a reply reserve (start with 512, tunable).
3. **Trim in chunks.** When trimming triggers, trim down to about 75% of the budget instead of dropping one pair every turn. Believed, not verified: Ollama reuses the already-read start of the conversation between turns (`prompt_eval_cached_count`), and removing messages from the front invalidates that reuse, so frequent small trims would make every turn re-read the whole history.
4. **Optional safety net, later:** compare the tokens Ollama says it read (`prompt_eval_count` plus `prompt_eval_cached_count`) with what we sent. If it read far less, show the same visible "forgot early messages" note. This catches errors in our estimate. It needs a new optional field on `Reply` (allowed by [ADR 0008](0008-reply-object.md)). Not built until the session and trimming work.

## Related

- ADRs: [0007](0007-cli-structure.md), [0008](0008-reply-object.md) (`Usage` is the calibration source), [0010](0010-timeouts-and-retries.md).
- Open questions: 6 (closed here), 12 (partly decided), 15 and 16 (new).
- plan.md: section 13 Month 2 Week 1.
- Implementation hand-off (code session), in this order:
  1. Experiment: a long chat with a fact at the start; observe what Ollama does past 4096 tokens, and whether `options.num_ctx` is honored. **Done 2026-11-20** (see the update section).
  2. A `Session` object (messages plus system prompt) with tests.
  3. `prompts/system.txt`, its loader, and a test that no conversation text reaches the template.
  4. Trimming with the priority order, whole pairs, and a visible notice; tests for each rule.
  5. `LOCAL_AI_CONTEXT_TOKENS` in `Settings` and `.env.example`; the adapter sends `num_ctx`.
  6. Switch `run_chat` to the session; update tests, request-flow and trust-boundaries.
