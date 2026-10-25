# 0007: CLI structure: factory function, injected I/O, rollback on failure, exit codes

- **Status:** Accepted (retroactive)
- **Date:** 2026-10-26 (Block 2)
- **Recorded:** 2026-10-26

## Context and forces

- The CLI is the first interface; voice comes in Month 4, and maybe web later.
- It must be testable without a keyboard, a screen or a model.
- Failures must be understandable and must not leak secrets.

## Options considered and decisions

This ADR groups several small, related Block 2 decisions.

### Choosing the provider
- **Chosen: one `build_provider(settings)` function** in `providers/factory.py`. It is the only place that maps a name to a class.
- Alternative: a registry (providers register themselves by name). More flexible, but an extra layer with only one real provider.
- Alternative: the CLI picks the class itself. Simpler, but the CLI would import every adapter.

### Testability
- **Chosen: `run_chat(provider, input_fn, output_fn)`**, with input and output passed in.
- Alternative: monkeypatch `input` and `print` in tests. The Block 2 page records why this failed: default arguments are evaluated once, at definition time.

### A failed turn
- **Chosen:** if `generate()` raises `ProviderError`, the unanswered user message is removed from history and the loop continues.
- Alternative: keep it. A retry would then send two user messages in a row.

### Errors and exit codes
- **Chosen:** exit code 0 = ok, 1 = provider problem, 2 = config problem. Only `ProviderError` is caught in the loop; anything else is a bug and shows a traceback on purpose (fail loud). Config errors print the field name and reason, never the value.

### Who owns the conversation history
- **Chosen (implicitly, inferred):** `run_chat` keeps it as a local `list[Message]`. No session object exists.

## Why

From the Block 2 page: "No extra layers until needed"; "Tests need no keyboard, screen or model"; "A retry never leaves two user turns in a row"; "Scripts and tests can tell failures apart."

## Consequences and trade-offs accepted

- Conversation logic lives inside the CLI. A second interface (voice) would have to repeat it or move it out.
- The CLI imports `Message`, so it knows the provider's data model.
- History lives only for one run; nothing is saved.

## What would make us revisit this

- **Month 2 Week 1 (sessions and system prompt):** decide who owns history (mentoring topic 2).
- **Month 4 (voice):** a second interface needs the same conversation logic.
- **Month 1 Week 3:** the factory gets real branches; the "not implemented" `ProviderError` and its temporary test go away.

## Related

- ADRs: [0006](0006-sync-str-return.md).
- plan.md: section 13 Month 1 Week 2, Month 2 Week 1, Month 4.
- Build page: [20261026_block2.md](../../Build/20261026_block2.md).
