# W.I.N.T.E.R — Design

This folder records **why** W.I.N.T.E.R is built the way it is: the decisions, the alternatives that were considered, and the trade-offs accepted. The code shows *what* was built; [docs/Build/](../Build/) shows *when*; this folder shows *why*.

It is written in architecture-mentoring sessions. No code lives here. When a decision needs code, the ADR includes an "Implementation hand-off" note for the code session.

## How to read this folder

| Path | What it holds |
|---|---|
| [decisions/](decisions/) | Architecture Decision Records (ADRs): one decision per file, numbered. Start with the index below. |
| [decisions/0000-template.md](decisions/0000-template.md) | The empty template for a new ADR. |
| [diagrams/](diagrams/) | Context, request flow, and trust boundaries, as built today. |
| [open-questions.md](open-questions.md) | Undecided questions and assumptions, each with the trigger that should reopen it. |
| [learning-notes.md](learning-notes.md) | Plain-language notes on design concepts, tied to W.I.N.T.E.R examples. |

### ADR rules

- One decision per file: `NNNN-short-title.md`, numbered in order from 0001.
- Never delete or rewrite an accepted ADR. When a decision changes, write a new ADR and mark the old one "Superseded by NNNN".
- **Accepted (retroactive)** means the decision was made before this folder existed and was written up afterwards. Text marked *(inferred)* was reconstructed and needs Sridhar to confirm it.
- **Deferred** means the decision is deliberately postponed; the ADR names the trigger.

## Decision index

| ID | Title | Status | Date |
|---|---|---|---|
| [0001](decisions/0001-python-version.md) | Python 3.13 for development, 3.11 as the minimum | Accepted (retroactive) | 2026-10-19 |
| [0002](decisions/0002-venv-requirements.md) | venv and requirements.txt (not uv) | Accepted (retroactive) | 2026-10-19 |
| [0003](decisions/0003-pydantic-settings.md) | pydantic-settings for validated configuration | Accepted (retroactive) | 2026-10-19 |
| [0004](decisions/0004-ollama-first.md) | Ollama first, native on Windows; OpenRouter second | Accepted (retroactive) | 2026-10-19 |
| [0005](decisions/0005-provider-abc.md) | Provider interface as an ABC | Accepted (retroactive) | 2026-10-26 |
| [0006](decisions/0006-sync-str-return.md) | Provider contract: sync `generate() -> str`, one `ProviderError` | Accepted (retroactive); return type superseded by 0008, errors by 0009; sync call stands | 2026-10-26 |
| [0007](decisions/0007-cli-structure.md) | CLI structure: factory, injected I/O, rollback, exit codes | Accepted (retroactive); exit-code part partially superseded by 0009 | 2026-10-26 |
| [0008](decisions/0008-reply-object.md) | Provider returns a `Reply` object (text, stop reason, usage) | Accepted | 2026-10-26 |
| [0009](decisions/0009-provider-error-hierarchy.md) | Provider errors: small hierarchy grouped by caller action | Accepted | 2026-10-26 |
| [0010](decisions/0010-timeouts-and-retries.md) | Timeouts and retries: one wrapper layer, never retry actions | Accepted | 2026-10-26 |

## Mentoring topics

1. Provider boundary (**in progress**)
2. Conversation and state
3. Orchestrator
4. Tool system and permissions
5. Memory
6. Interfaces and process model
7. Observability and cost
8. Config and deployment
