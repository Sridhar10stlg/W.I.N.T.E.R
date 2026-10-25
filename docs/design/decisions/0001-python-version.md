# 0001: Python 3.13 for development, 3.11 as the minimum

- **Status:** Accepted (retroactive)
- **Date:** 2026-10-19
- **Recorded:** 2026-10-26

## Context and forces

- Four laptops: the Dynabook (32GB), the 4GB Dell, a laptop not yet bought, and a MacBook in about 4 years. They will not always have the same Python installed.
- Newer Python versions are faster and have nicer syntax, but every feature used becomes a requirement on every laptop.
- The minimum version is a promise to every machine that installs W.I.N.T.E.R. Raising it later is easy; lowering it later means removing code that relies on newer features.

## Options considered

### Option A: develop on 3.13, allow `>=3.11` (chosen)
- **Pros:** the newest Python on the main laptop; older laptops are not blocked by a minor version difference.
- **Cons:** the floor is only a promise. Nothing tests on 3.11 today, so 3.12+/3.13-only syntax could slip in unnoticed.
- **Makes hard later:** nothing much. Raising the floor is a one-line change.

### Option B: 3.13 only (`>=3.13`)
- **Pros:** what you develop on is exactly what you support. No hidden version bugs.
- **Cons:** every laptop must install 3.13 before it can run anything.
- **Makes hard later:** onboarding an older machine.

### Option C: develop on 3.11 (the floor itself)
- **Pros:** the floor is tested every day.
- **Cons:** older interpreter on the main laptop; loses newer conveniences for no current benefit. *(Inferred: not considered at the time.)*
- **Makes hard later:** nothing.

## Decision

Develop on Python 3.13. `pyproject.toml` declares `requires-python = ">=3.11"`.

## Why

From the Block 1 page: "The lower floor keeps the 4GB Dell and a future Mac from being blocked by a minor version difference."

## Consequences and trade-offs accepted

- Code must avoid syntax newer than 3.11 (for example the 3.12 `type` statement and `class Foo[T]` generics).
- Until something runs the tests on 3.11, the floor is untested. That is a known gap, not a guarantee.

## What would make us revisit this

- **Month 6, Week 2 (continuous integration):** either run the tests on 3.11 as well as 3.13, or raise the floor to match what is actually tested.
- A laptop that cannot run 3.11 or later.

## Related

- plan.md: section 13, Month 1 Week 1 and Month 6 Week 2.
- Build page: [20261019_block1.md](../../Build/20261019_block1.md).
