# 0002: venv and requirements.txt for dependencies (not uv)

- **Status:** Accepted (retroactive)
- **Date:** 2026-10-19
- **Recorded:** 2026-10-26

## Context and forces

- The same setup must work on Windows laptops now and a Mac later.
- A solo developer should spend time on W.I.N.T.E.R, not on learning a packaging tool.
- Reproducibility (the same versions on every laptop) matters more as the project grows.

## Options considered

### Option A: `python -m venv` + `requirements.txt` with version ranges (chosen)
- **Pros:** built into Python; nothing extra to install; works the same everywhere.
- **Cons:** ranges like `pydantic>=2.7,<3` are not a lock. Two laptops can end up with different versions.
- **Makes hard later:** exact reproducibility, until a lock or pin step is added.

### Option B: uv
- **Pros:** very fast; creates the venv and a lock file in one tool.
- **Cons:** one more tool to install on every laptop and to learn.
- **Makes hard later:** nothing serious. Migration from requirements.txt is straightforward.

### Option C: Poetry or pip-tools
- **Pros:** lock files and dependency resolution.
- **Cons:** more ceremony than the project needs at this stage. *(Inferred: not considered at the time.)*
- **Makes hard later:** nothing serious.

## Decision

Use a standard `venv` with `requirements.txt`. The package itself is installed with `pip install -e .`.

## Why

From the Block 1 page: "Simplest, works the same on all four laptops."

## Consequences and trade-offs accepted

- Dependencies are listed in `requirements.txt`, not in `pyproject.toml` `[project.dependencies]`. So `pip install -e .` on its own installs no dependencies; `pip install -r requirements.txt` must run first. Setup notes must keep saying that.
- Versions can drift between laptops within the allowed ranges.

## What would make us revisit this

- **Month 6, Week 2 (dependency pinning).**
- A bug that appears on one laptop but not another because of a different library version.
- Setup taking more than a few minutes on a new laptop.

## Related

- ADR: [0001](0001-python-version.md).
- plan.md: section 4 (Packaging), section 13 Month 6 Week 2.
- Build page: [20261019_block1.md](../../Build/20261019_block1.md).
