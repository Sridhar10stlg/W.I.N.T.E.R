# 0011: httpx as the HTTP library for model adapters

- **Status:** Accepted
- **Date:** 2026-11-19
- **Recorded:** 2026-11-19

## Context and forces

- The Ollama adapter (Block 3) and, later, the OpenRouter adapter must make HTTP calls.
- [ADR 0010](0010-timeouts-and-retries.md) needs every call to have a timeout, and needs a timeout to be told apart from "nobody home".
- Unit tests must run with no real server (project testing rules).
- Month 2 adds streaming replies (open question 4).
- Project rule: add a dependency only with a concrete need, and explain it.

## Options considered

- **`urllib` (standard library):** no new dependency, but timeouts and error types are clumsy, and tests need hand-built fakes.
- **`requests`:** familiar, but no built-in way to fake the network, and no async or streaming story as clean as `httpx`.
- **The official `ollama` Python package:** short code, but it only covers Ollama. OpenRouter would need a second approach, and the package hides the HTTP layer our error mapping depends on.
- **`httpx` (chosen).**

## Decision

Use `httpx`, constrained to `>=0.27,<1` in `requirements.txt`. It is imported in the adapter files only (`providers/ollama.py` today), never in the CLI, `Settings` or `RetryingProvider`.

## Why

- Distinct exception classes: `TimeoutException` (retryable, [ADR 0009](0009-provider-error-hierarchy.md) temporary) versus `ConnectError` (Ollama not running, unavailable). This maps directly onto the error hierarchy.
- `httpx.MockTransport` lets the whole adapter run in tests with the network faked at the lowest level (34 adapter tests, no Ollama needed).
- The same library serves OpenRouter and can stream later.

## Consequences and trade-offs accepted

- One direct dependency plus its helpers (`httpcore`, `h11`, `anyio`, `certifi`, `idna`).
- `httpx` exceptions are not all in one family: `InvalidURL` is outside `HTTPError`. A test found this on 2026-11-19, so the adapter validates the address when it is built instead of relying on `except`.
- A single `timeout=` number applies to each phase (connect, write, read, pool). For a non-streaming call the read phase is the model thinking, which is what we want. Streaming (Month 2) will need a second look.

## What would make us revisit this

- A security issue or breaking release in `httpx`.
- Streaming needs behaviour the sync client does not offer well.

## Related

- ADRs: [0004](0004-ollama-first.md), [0009](0009-provider-error-hierarchy.md), [0010](0010-timeouts-and-retries.md).
- plan.md: section 13 Month 1 Week 3.
