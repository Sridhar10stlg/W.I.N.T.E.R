# W.I.N.T.E.R — Progress Index

Master index for the build history. Each block of work has its own detailed page in [docs/Build/](Build/). This file only lists them and records where we are.

- **Deadline:** 2027-10-19 (12 months from 2026-10-19). Schedule: [plan.md](../plan.md), section 13.
- **Working method:** AI supplies paste-ready code block by block; Sridhar reads, pastes, runs, and learns. Rules: [AI_Guidelines.md](../AI_Guidelines.md), [CLAUDE.md](../CLAUDE.md).
- **Naming:** `yyyymmdd_block{n}.md` (the date the block was done, e.g. `20261019_block1.md`). After each block: add the page, then add a row below.

## Current position

**Next up:** Month 1, Week 2, Block 2 (provider interface, mock provider, CLI loop). Code was supplied; verification not yet recorded.

## Build index

| Month | Week | Block | Topic | Status | Page |
|---|---|---|---|---|---|
| 0 | n/a | Setup | Repository rules, `.gitignore`, `.gitattributes`, branches, plan | Done | [20261012_setup.md](Build/20261012_setup.md) |
| 1 | 1 | 1 | Project skeleton and validated configuration | Done | [20261019_block1.md](Build/20261019_block1.md) |
| 1 | 2 | 2 | Provider interface, mock provider, CLI loop | In progress | pending |
| 1 | 3 | 3 | Ollama adapter with clear errors | Planned | pending |
| 1 | 4 | 4 | Logging with secret redaction, failure tests | Planned | pending |

## Laptops

| # | Laptop | Specs | Notes |
|---|---|---|---|
| 1 | Dell Inspiron (personal, low spec) | 4GB RAM, 256GB SSD, 1TB HDD, Ryzen 3 | Use only `gemma3:1b`; install Ollama natively on Windows, not WSL |
| 2 | Dynabook (organization, high spec) | 32GB RAM, 900GB SSD, Intel i7 255H, 128MB graphics | Ollama runs in WSL; `gemma3:1b` and `gemma3:4b` installed |
| 3 | New personal high-end laptop | To be bought | Local-model benchmarks (Month 9) |
| 4 | New personal MacBook | In about 4 years | Keep code portable (`pathlib`, no hardcoded paths) |

## Open questions
- Which of `main` and `dev` do I use day to day? (`master` is deleted.)
