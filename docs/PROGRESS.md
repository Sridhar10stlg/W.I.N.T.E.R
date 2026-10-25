# W.I.N.T.E.R — Progress Index

Master index for the build history. Each block of work has its own detailed page in [docs/Build/](Build/). This file only lists them and records where we are.

- **Deadline:** 2027-10-19 (12 months from 2026-10-19). Schedule: [plan.md](../plan.md), section 13.
- **Working method:** AI supplies paste-ready code block by block; Sridhar reads, pastes, runs, and learns. Rules: [AI_Guidelines.md](../AI_Guidelines.md), [CLAUDE.md](../CLAUDE.md).
- **Naming:** `yyyymmdd_block{n}.md` (the date the block was done, e.g. `20261019_block1.md`). After each block: add the page, then add a row below.

## Current position

**Next up:** Month 1, Week 2 follow-up, Block 2b-1 (`Reply` and `Usage` objects). Block 2 is done and verified (22 tests passed on the Dynabook), but the design review ([docs/design/](design/)) decided the provider contract must change before the Ollama adapter. Order: 2b-1 `Reply`, 2b-2 error hierarchy, 2b-3 timeout and model-tier settings, 2b-4 `RetryingProvider`, then Block 3 (Ollama adapter).

Native Windows Ollama is installed on the Dynabook (v0.40.11) with `gemma3:1b` and `gemma3:4b` pulled. Neither lists a `tools` capability, which matters for Month 3 (see [plan.md](../plan.md)).

## Build index

| Month | Week | Block | Topic | Status | Page |
|---|---|---|---|---|---|
| 0 | n/a | Setup | Repository rules, `.gitignore`, `.gitattributes`, branches, plan | Done | [20261012_setup.md](Build/20261012_setup.md) |
| 1 | 1 | 1 | Project skeleton and validated configuration | Done | [20261019_block1.md](Build/20261019_block1.md) |
| 1 | 2 | 2 | Provider interface, mock provider, CLI loop | Done | [20261026_block2.md](Build/20261026_block2.md) |
| 1 | 2 | 2b-1 | `Reply` and `Usage`; safe terminal output ([ADR 0008](design/decisions/0008-reply-object.md)) | Planned | pending |
| 1 | 2 | 2b-2 | Error hierarchy, exit code 2 for setup problems ([ADR 0009](design/decisions/0009-provider-error-hierarchy.md)) | Planned | pending |
| 1 | 2 | 2b-3 | Timeout and model-tier settings | Planned | pending |
| 1 | 2 | 2b-4 | `RetryingProvider` ([ADR 0010](design/decisions/0010-timeouts-and-retries.md)) | Planned | pending |
| 1 | 3 | 3 | Ollama adapter with clear errors | Planned | pending |
| 1 | 4 | 4 | Logging with secret redaction, failure tests | Planned | pending |

## Laptops

| # | Laptop | Specs | Notes |
|---|---|---|---|
| 1 | Dell Inspiron (personal, low spec) | 4GB RAM, 256GB SSD, 1TB HDD, Ryzen 3 | Use only `gemma3:1b`; install Ollama natively on Windows, not WSL |
| 2 | Dynabook (organization, high spec) | 32GB RAM, 900GB SSD, Intel i7 255H, 128MB graphics | Ollama runs natively on Windows (per-user install, v0.40.11, no admin needed); `gemma3:1b` and `gemma3:4b` pulled. The old WSL Ubuntu Ollama has its own separate models; keep WSL stopped because both use port 11434 |
| 3 | New personal high-end laptop | To be bought | Local-model benchmarks (Month 9) |
| 4 | New personal MacBook | In about 4 years | Keep code portable (`pathlib`, no hardcoded paths) |

## Decisions
- **Branches:** `dev` is the day-to-day working branch. `main` is for releases only. (`master` is deleted.)

## Open questions
- Tracked in [docs/design/open-questions.md](design/open-questions.md) (design questions, each with the plan month that should reopen it). Pending for the code work: the `httpx` dependency for the Ollama adapter.
