# W.I.N.T.E.R — Progress Index

Master index for the build history. Each block of work has its own detailed page in [docs/Build/](Build/). This file only lists them and records where we are.

- **Deadline:** 2027-11-09 (moved from 2027-10-19 on 2026-11-18 after a ~3-week Month 1 slip). Schedule: [plan.md](../plan.md), section 13.
- **Working method:** AI supplies paste-ready code block by block; Sridhar reads, pastes, runs, and learns. Rules: [AI_Guidelines.md](../AI_Guidelines.md), [CLAUDE.md](../CLAUDE.md).
- **Naming:** `yyyymmdd_block{n}.md` (the date the block was done, e.g. `20261019_block1.md`). After each block: add the page, then add a row below.

## Current position

**Next up:** Month 2 Week 1: conversation/session handling, system prompt, and a history size limit (design open questions 6 and 12). Month 1 is complete: Blocks 2b-1 to 2b-4 and Block 3 are done and verified (94 tests passed on the Dynabook). W.I.N.T.E.R now has a real local model: `python -m winter` chats with `gemma3:4b` through Ollama. Still to do from the plan: the OpenRouter adapter (must work before Month 3 Week 4) and logging (Month 2 Week 2).

Native Windows Ollama is installed on the Dynabook (v0.40.11) with `gemma3:1b` and `gemma3:4b` pulled. Neither lists a `tools` capability, which matters for Month 3 (see [plan.md](../plan.md)).

## Build index

| Month | Week | Block | Topic | Status | Page |
|---|---|---|---|---|---|
| 0 | n/a | Setup | Repository rules, `.gitignore`, `.gitattributes`, branches, plan | Done | [20261012_setup.md](Build/20261012_setup.md) |
| 1 | 1 | 1 | Project skeleton and validated configuration | Done | [20261019_block1.md](Build/20261019_block1.md) |
| 1 | 2 | 2 | Provider interface, mock provider, CLI loop | Done | [20261026_block2.md](Build/20261026_block2.md) |
| 1 | 2 | 2b-1 | `Reply` and `Usage`; safe terminal output ([ADR 0008](design/decisions/0008-reply-object.md)) | Done | [20261119_block2b.md](Build/20261119_block2b.md) |
| 1 | 2 | 2b-2 | Error hierarchy, exit code 2 for setup problems ([ADR 0009](design/decisions/0009-provider-error-hierarchy.md)) | Done | [20261119_block2b.md](Build/20261119_block2b.md) |
| 1 | 2 | 2b-3 | Timeout and model-tier settings | Done | [20261119_block2b.md](Build/20261119_block2b.md) |
| 1 | 2 | 2b-4 | `RetryingProvider`, wired in `build_provider` ([ADR 0010](design/decisions/0010-timeouts-and-retries.md)) | Done | [20261119_block2b.md](Build/20261119_block2b.md) |
| 1 | 3 | 3 | Ollama adapter with clear errors ([ADR 0011](design/decisions/0011-httpx-for-http.md)) | Done | [20261119_block3.md](Build/20261119_block3.md) |
| 1 | 4 | 4 | Logging with secret redaction, failure tests | Moved to Month 2 Week 2 | pending |

## Laptops

| # | Laptop | Specs | Notes |
|---|---|---|---|
| 1 | Dell Inspiron (personal, low spec) | 4GB RAM, 256GB SSD, 1TB HDD, Ryzen 3 | Use only `gemma3:1b`; install Ollama natively on Windows, not WSL |
| 2 | Dynabook (organization, high spec) | 32GB RAM, 900GB SSD, Intel i7 255H, 128MB graphics | Ollama runs natively on Windows (per-user install, v0.40.11, no admin needed); `gemma3:1b` and `gemma3:4b` pulled. The old WSL Ubuntu Ollama has its own separate models; keep WSL stopped because both use port 11434 |
| 3 | New personal high-end laptop | To be bought | Local-model benchmarks (Month 9) |
| 4 | New personal MacBook | In about 4 years | Keep code portable (`pathlib`, no hardcoded paths) |

## Decisions
- **Branches:** `dev` is the day-to-day working branch. `main` is for releases only. (`master` is deleted.)
- **2026-11-18, schedule:** v1.0 deadline moved from 2027-10-19 to 2027-11-09 (Month 1 slipped ~3 weeks). Order: 2b-1 → 2b-4 → Ollama adapter (Block 3); 2b-1 to 2b-4 finished 2026-11-19, so the slip did not grow. Logging moves to Month 2 Week 2; OpenRouter must work before Month 3 Week 4.
- **2026-11-19, HTTP library:** `httpx` for the Ollama (and later OpenRouter) adapter. Offline tests with `MockTransport`, clear timeout errors, can stream later. Details on the Block 3 build page.

## Open questions
- Tracked in [docs/design/open-questions.md](design/open-questions.md) (design questions, each with the plan month that should reopen it).