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

## Retries: one layer only, and only if safe to repeat

- **Retry amplification:** if two layers each try 3 times, one question makes 3 × 3 = 9 calls. Retry in one place only (W.I.N.T.E.R: a `RetryingProvider` wrapper).
- **Idempotency:** safe to repeat = doing it twice has the same effect as once. Asking the model is safe. Sending a message is not: a timeout may mean it *was* sent. Never auto-retry actions; ask the user.

## Safe error messages

- **What:** error messages are output, so they follow the same rules as any output: no secrets, no untrusted raw data.
- **Rules:** say what happened plus how to fix it; never print a raw server response; never print any part of a key (a prefix is still a secret); strip credentials from URLs.
