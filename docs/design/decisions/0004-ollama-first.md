# 0004: Ollama first, running natively on Windows; OpenRouter second

- **Status:** Accepted (retroactive)
- **Date:** 2026-10-19 (Ollama first); October 2026 (moved from WSL to native Windows on the Dynabook)
- **Recorded:** 2026-10-26

## Context and forces

- Hosted APIs cost money on every call; local models are free but weaker and slower.
- The 4GB Dell can only run a very small model (`gemma3:1b`).
- plan.md wants model access behind one provider interface, so the backend can be swapped.
- Month 3 needs a model that can propose tool calls.

## Options considered

### Option A: Ollama first, OpenRouter after it works (chosen)
- **Pros:** free while learning and testing; works offline; exercises real failure cases (server not running, model not found, timeouts).
- **Cons:** small local models give weaker answers; tool-calling support depends on the model.
- **Makes hard later:** nothing, as long as the provider interface stays backend-neutral.

### Option B: OpenRouter first
- **Pros:** strong models immediately; tool calling widely available.
- **Cons:** costs money from day one; needs a network connection and a key.
- **Makes hard later:** nothing.

### Option C: one OpenAI-compatible adapter for both
- **How it works:** Ollama also offers an OpenAI-style endpoint, so one adapter could talk to both backends with a different base URL. *(Inferred and not verified: check the endpoint on Ollama v0.40.11 before relying on it.)*
- **Pros:** one adapter instead of two.
- **Cons:** limited to features both sides share; Ollama-specific errors may be less clear.
- **Makes hard later:** using backend-specific features.

### Sub-decision: where Ollama runs on the Dynabook
- **WSL (original):** worked, but added a layer between Windows and the model.
- **Native Windows (current):** per-user install, v0.40.11, no admin needed. The Dell will use the same approach.

## Decision

Build the Ollama adapter first (Month 1 Week 3), then OpenRouter. Ollama runs natively on Windows. Models: `gemma3:1b` (low) and `gemma3:4b` (high, default on the Dynabook). Bigger models wait for the Month 9 benchmarks.

## Why

- From the Block 1 page: "No cost while learning. Both sit behind one provider interface later."
- From Sridhar (2026-10-26): fast replies matter more than answer quality while building the loop, the adapter and the tests; testing 12b now would distract from Weeks 3 and 4.

## Consequences and trade-offs accepted

- The old WSL Ollama still exists with its own models, and both use port 11434. If WSL starts first, W.I.N.T.E.R silently talks to the wrong server. Keep WSL stopped. The Week 3 adapter's "model not found" error is the first line of defence.
- **Unverified:** gemma3 may not support tool calling in Ollama. Check with `ollama show gemma3:1b` (and `gemma3:4b` once pulled). If tools are not listed, Month 3 needs a different local model or OpenRouter.

## What would make us revisit this

- `ollama show` confirms gemma3 has no tool support (decide before Month 3).
- Month 9 benchmarks.
- Local replies too slow on the Dell to be usable.

## Related

- ADRs: [0006](0006-sync-str-return.md) (the interface the adapter must implement).
- plan.md: section 13 Month 1 Week 3, Month 3, Month 9.
- Build pages: [20261019_block1.md](../../Build/20261019_block1.md), [20261026_block2.md](../../Build/20261026_block2.md).
