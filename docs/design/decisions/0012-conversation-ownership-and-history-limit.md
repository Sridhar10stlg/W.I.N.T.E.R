# 0012: Conversation ownership and the history limit

- **Status:** Accepted
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
- **Window setting:** a new `LOCAL_AI_CONTEXT_TOKENS` (default 4096) drives our budget, and the Ollama adapter sends the same number as `num_ctx`, so our budget and the server's window cannot disagree. (Assumes `/api/chat` honors `options.num_ctx`; verified in the first experiment.)
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

## Related

- ADRs: [0007](0007-cli-structure.md), [0008](0008-reply-object.md) (`Usage` is the calibration source), [0010](0010-timeouts-and-retries.md).
- Open questions: 6 (closed here), 12 (partly decided), 15 and 16 (new).
- plan.md: section 13 Month 2 Week 1.
- Implementation hand-off (code session), in this order:
  1. Experiment: a long chat with a fact at the start; observe what Ollama does past 4096 tokens, and whether `options.num_ctx` is honored.
  2. A `Session` object (messages plus system prompt) with tests.
  3. `prompts/system.txt`, its loader, and a test that no conversation text reaches the template.
  4. Trimming with the priority order, whole pairs, and a visible notice; tests for each rule.
  5. `LOCAL_AI_CONTEXT_TOKENS` in `Settings` and `.env.example`; the adapter sends `num_ctx`.
  6. Switch `run_chat` to the session; update tests, request-flow and trust-boundaries.
