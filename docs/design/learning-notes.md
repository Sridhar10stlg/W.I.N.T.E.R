# Learning notes

Short, plain-language notes on design concepts, each tied to a real W.I.N.T.E.R example. Newest at the bottom.

## YAGNI: "You Aren't Gonna Need It"

- **What:** don't build something because you *might* need it later. Build it when you actually need it. From Extreme Programming (late 1990s).
- **Why:** "just in case" code costs time now, is often built for a need that turns out different, and still has to be read, tested and maintained.
- **W.I.N.T.E.R examples:** no tool registry before Month 2; no database before Month 5; `build_provider()` is a function, not a plugin registry; no 12b model testing before Month 9.
- **Watch out:** YAGNI is about not building *features*. It is not permission to close doors. Test: *does keeping the door open cost almost nothing now, while closing it costs a lot later?* If yes, keep it open, but still don't build what's behind it.
- **Related:** KISS ("Keep It Simple"). YAGNI is about *what* you build, KISS about *how*.

## Contracts vs. implementations

- **What:** a contract is what one part of the system promises the others. An implementation is how it keeps that promise.
- **Why it matters:** implementations are cheap to change (one file knows about them). Contracts are expensive (everything on both sides depends on them). Architecture is mostly picking the few contracts and getting them right.
- **W.I.N.T.E.R example:** `Provider.generate(...)` is a contract. How the Ollama adapter talks HTTP is an implementation.

## One-way and two-way doors (reversibility)

- **What:** a two-way door is a decision you can cheaply undo. A one-way door is expensive or impossible to undo.
- **Why it matters:** decide two-way doors quickly; slow down for one-way doors. A contract starts as a two-way door and turns into a one-way door as more code depends on it.
- **W.I.N.T.E.R example:** ABC vs. Protocol is a two-way door. The return type of `generate()` is turning into a one-way door as adapters and tests are written against it.

## The last responsible moment

- **What:** delay a decision until the cost of delaying becomes higher than the cost of deciding.
- **Why it matters:** decide too early and you guess; decide too late and the decision is made for you by the code that already exists.
- **W.I.N.T.E.R example:** the provider return type should be settled before the Ollama adapter (Week 3), even though tool calls are Month 3.

## Extend by adding, not by changing

- **What:** a good contract grows by adding things (a new optional field), so nothing that already uses it breaks. A brittle one grows by changing things (a new type), which breaks every user.
- **W.I.N.T.E.R example:** a result object with a `text` field can gain `usage` later without breaking anyone; a bare `str` cannot.

## Boundaries decide what information survives

- **What:** whatever a boundary does not pass along is lost to the rest of the system.
- **Why it matters:** when needed information is dropped, people build side channels (hidden state, globals, parsing strings), and those cause bugs and security holes.
- **W.I.N.T.E.R example:** Ollama returns token counts with each reply. With `-> str`, the adapter must throw them away, but Month 2 needs them for cost measurement.

## Model output is untrusted, including plain text

- **What:** anything that came from the model, or from anything the model read, is data, never instructions.
- **The trap:** tool-call arguments obviously need checking because they drive actions. Reply text looks harmless, but it can manipulate the human reading it, flows back into history, memory and speech, and can carry terminal control characters.
- **W.I.N.T.E.R example:** in `Reply`, `text` is untrusted; the time a call took is measured by the app and is trusted.

## Decide the shape, not the contents

- **What:** you can't build a contract "correct the first time", because future needs are unknown. Choose a container that can grow, fill it with what you have today, and add the rest when it is needed.
- **W.I.N.T.E.R example:** [ADR 0008](decisions/0008-reply-object.md): `Reply` holds text, stop reason and usage now; tool calls are added in Month 3.

## Anti-corruption layer

- **What:** an adapter translates an outside system's vocabulary into your own, so the outside system's names and quirks never spread into your code.
- **W.I.N.T.E.R example:** Ollama and OpenRouter name the stop reason and token counts differently. Each adapter converts them into `Reply.stop_reason` and `Reply.usage`; nothing outside the adapter sees vendor field names.

## Group errors by what the caller can do

- **What:** design error types around the caller's decision (retry, fix setup, it's a bug), not the technical cause (network, HTTP, JSON).
- **Why:** if the type doesn't carry the decision, the caller reads message strings to guess ("stringly-typed"), which breaks silently when a message is reworded.
- **W.I.N.T.E.R example:** [ADR 0009](decisions/0009-provider-error-hierarchy.md): timeout → temporary (retry once); model not found → setup (never retry).
- **Self-check habit:** compare your own answers against each other. "Retry timeouts" plus "one error type" was a contradiction that only shows up when you put the two side by side.

## Fail loud, not silent

- **What:** when something fails, stop and say so clearly. Never quietly substitute something else.
- **W.I.N.T.E.R example:** if the configured provider has no adapter, stop at startup. Silently falling back to the mock would make you believe you were talking to a real model. Same family as the Block 1 bug where `extra="ignore"` hid a misnamed variable.

## Substitutability ("is a") and except order

- **What:** a subclass *is a* kind of its parent, so it can be used anywhere the parent is expected. A "Dogs allowed" sign lets a Labrador in.
- **W.I.N.T.E.R example:** `ProviderTemporaryError` is a `ProviderError`, so `run_chat`'s existing `except ProviderError` still catches it, with no change.
- **Trap:** Python checks `except` lines top to bottom and uses the **first** match. Put the specific type first and the general type last, or the specific handler never runs.

## Wrapper (decorator) pattern

- **What:** an object that *is a* Provider and *has a* Provider inside. It passes calls through and adds one behaviour around them.
- **W.I.N.T.E.R example:** `RetryingProvider(inner)` (Block 2b-4) adds the retry; the CLI can't tell it from a plain provider. `build_provider` is the only place that wraps, so no provider reaches the CLI unwrapped.
- **Why it's good:** the retry rule lives in one place, and every future adapter gets it for free.

## Clean at the output boundary, not in storage

- **What:** transform data for where it is going, at the moment it goes there. Keep the stored copy original.
- **W.I.N.T.E.R example:** `safe_for_terminal()` cleans reply text only when printing; history keeps the raw text for the model.

## Retries: one layer only, and only if safe to repeat

- **Retry amplification:** if two layers each try 3 times, one question makes 3 × 3 = 9 calls. Retry in one place only (W.I.N.T.E.R: a `RetryingProvider` wrapper).
- **Idempotency:** safe to repeat = doing it twice has the same effect as once. Asking the model is safe. Sending a message is not: a timeout may mean it *was* sent. Never auto-retry actions; ask the user.

## Safe error messages

- **What:** error messages are output, so they follow the same rules as any output: no secrets, no untrusted raw data.
- **Rules:** say what happened plus how to fix it; never print a raw server response; never print any part of a key (a prefix is still a secret); strip credentials from URLs.

## Single source of truth: who owns shared state

- **What:** a rule that must behave the same everywhere lives in one place. Copies drift apart, and a bug fix has to be made once per copy.
- **W.I.N.T.E.R example:** [ADR 0012](decisions/0012-conversation-ownership-and-history-limit.md): one session object owns the conversation, not one list per interface (CLI, voice, web). Same idea as `RetryingProvider` for retries.
- **Trap:** "simplest today" and "simplest overall" are different. Needed in 3 places later? Put it in 1 now, if it is cheap.

## Build the simple version first; keep the powerful one as a planned upgrade

- **What:** fix the real problem with the least machinery, and write the bigger idea down as a follow-up with a trigger.
- **W.I.N.T.E.R example:** a long chat drops the oldest exchanges and says so (ADR 0012). Summarising is more powerful, but it adds a model call, can distort facts, and its output is untrusted. It is open question 15, not forgotten. Same for Jinja2 over `string.Template` (open question 16).

## Invariants

- **What:** a rule that must be true after every operation, so the data is always valid.
- **W.I.N.T.E.R example:** the history is always whole question-and-answer pairs. Trimming drops pairs, never half of one. The rollback in `run_chat` (`history.pop()`) protects the same invariant.
- **Priority order:** when space is short, decide in advance who wins (system prompt, newest message, first message, recent exchanges). Otherwise a huge item can crowd out the important ones.

## Two numbers that must agree

- **What:** when two parts of a system each hold a limit, one of them is a copy, and copies disagree.
- **W.I.N.T.E.R example:** our trimming budget and Ollama's context window. One setting (`LOCAL_AI_CONTEXT_TOKENS`) drives both, so we cannot silently exceed what the server really reads.

## Template engines run logic

- **What:** a template engine does more than fill blanks; it can run conditions and loops. Untrusted text rendered inside a template can change what the template does.
- **Rule:** templates receive only values we supply. Conversation text, web pages and model output are added as separate messages, never rendered into a template.
- **W.I.N.T.E.R example:** the system prompt is a text file changed only by editing it (reviewed in git), never by a chat command or by model output.
