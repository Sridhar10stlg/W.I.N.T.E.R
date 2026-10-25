# 0003: pydantic-settings for validated configuration

- **Status:** Accepted (retroactive)
- **Date:** 2026-10-19
- **Recorded:** 2026-10-26

## Context and forces

- CLAUDE.md: validate all configuration, keep secrets out of logs, read secrets from the environment.
- Each laptop needs different values (model, Ollama URL) with no code change.
- A wrong setting should fail loudly at startup, not silently fall back to a default.

## Options considered

### Option A: pydantic-settings `Settings` class (chosen)
- **How it works:** one class with typed fields; values come from environment variables, then `.env`, then defaults.
- **Pros:** typed validation; `Literal` rejects typos; `SecretStr` hides the API key in `repr()`; cross-field checks (OpenRouter needs a key).
- **Cons:** a dependency; some hidden behaviour (environment variables silently override `.env`; `extra="ignore"` silently skips unknown names).
- **Makes hard later:** little. Pydantic is already a dependency, so it is the natural choice for tool input schemas too (topic 4).

### Option B: `os.environ` + a plain dataclass
- **Pros:** no dependency; nothing hidden.
- **Cons:** every check, type conversion and secret-hiding rule written by hand.
- **Makes hard later:** keeping validation consistent as settings grow.

### Option C: a TOML or YAML config file
- **Pros:** supports nested settings and per-laptop profile files.
- **Cons:** secrets must still come from the environment, so there would be two sources. *(Inferred: not considered at the time.)*
- **Makes hard later:** nothing now. Can be layered on later (topic 8).

## Decision

All configuration is read and validated once by `Settings` in `src/winter/config.py`, through `load_settings()`. No other module reads `os.environ`.

## Why

From the Block 1 page: "Validated, typed settings; `SecretStr` hides the API key."

## Consequences and trade-offs accepted

- Two real bugs in Block 1 came from the hidden behaviour: `extra="ignore"` hid a variable-name mismatch, and an environment variable overrode a `.env` typo. Both are now covered by tests and lessons in the Block 1 page.
- `"mock"` is a valid production setting (added in Block 2) so the app can run with no model installed. That is a test helper living in user configuration, accepted for convenience.

## What would make us revisit this

- Per-laptop profiles become painful to manage with flat environment variables (topic 8).
- A secret ever appears in output despite `SecretStr`.

## Related

- plan.md: section 4 (Configuration), section 13 Month 1 Week 1.
- Build pages: [20261019_block1.md](../../Build/20261019_block1.md), [20261026_block2.md](../../Build/20261026_block2.md).
