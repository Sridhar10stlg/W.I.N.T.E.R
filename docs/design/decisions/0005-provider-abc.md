# 0005: Provider interface as an abstract base class (ABC)

- **Status:** Accepted (retroactive)
- **Date:** 2026-10-26 (introduced in commit `4ee37b4`; `name` made abstract in Block 2)
- **Recorded:** 2026-10-26

## Context and forces

- plan.md: keep model providers behind a narrow interface so they can be replaced.
- The CLI and tests must work with any provider (mock, Ollama, OpenRouter) without knowing which.
- A provider that forgets part of the interface should fail early, not mid-conversation.
- This choice is cheap to change later (a two-way door): it affects one file and each adapter's class line.

## Options considered

### Option A: ABC with abstract `generate()` and abstract `name` (chosen)
- **How it works:** adapters inherit from `Provider`; Python refuses to create one that misses an abstract member.
- **Pros:** errors at construction time, at runtime, with no extra tools; explicit ("this class is a provider").
- **Cons:** every adapter must inherit from `Provider`.
- **Makes hard later:** using a class you don't control as a provider (it can't inherit).

### Option B: `typing.Protocol` (structural typing)
- **How it works:** any class with the right `name` and `generate()` counts as a provider; no inheritance.
- **Pros:** looser coupling; test fakes need no base class.
- **Cons:** checked only by a static type checker (mypy or pyright), and the project has none yet. Without one, a missing method is found only when it is called.
- **Makes hard later:** nothing.

### Option C: a plain function, `generate(messages) -> str`
- **Pros:** the simplest possible interface.
- **Cons:** nowhere to keep per-provider state (URL, model, HTTP client) except closures; no `name`.
- **Makes hard later:** adding more methods (for example streaming).

## Decision

`Provider` is an ABC in `src/winter/providers/base.py` with abstract `name` (property) and abstract `generate()`.

## Why

*(Inferred from code comments, please confirm or correct.)* An ABC makes Python refuse to create a provider that forgets `generate()` or `name`, so the mistake shows up immediately. Block 2 page: "A provider that forgets `name` fails at construction, not mid-chat." With no type checker in the project, runtime enforcement is the only enforcement available, which favours an ABC over a Protocol.

## Consequences and trade-offs accepted

- Adapters are coupled to the `Provider` class by inheritance.
- A test proves a provider without `name` cannot be created.

## What would make us revisit this

- A static type checker is added to the project (Protocol becomes equally safe and looser).
- A third-party class needs to act as a provider without inheriting.

## Related

- ADRs: [0006](0006-sync-str-return.md) (what `generate()` promises).
- Build page: [20261026_block2.md](../../Build/20261026_block2.md).
