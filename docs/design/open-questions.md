# Open design questions

Unresolved questions and assumptions to revisit. Each one has the trigger that should reopen it. When a question is decided, write an ADR and move it to the "Closed" section with a link.

| # | Question | Trigger to decide | Notes |
|---|---|---|---|
| 4 | Streaming: how will partial replies reach the CLI, and how do errors mid-stream behave? | Month 2 Week 2 | Matters most on the 4GB Dell. |
| 5 | Which model is used, `model_low` or `model_high`? Who decides? | Month 1 Week 3 | Both exist in `Settings`; nothing chooses between them. |
| 6 | Who owns conversation history and the system prompt: the CLI, a session object, or an orchestrator? | Month 2 Week 1 | Mentoring topic 2. Today `run_chat` owns it ([ADR 0007](decisions/0007-cli-structure.md)). |
| 7 | Does gemma3 support tool calling in Ollama? If not: another local model, or tools only via OpenRouter? | Before Month 3 | **Unverified.** Run `ollama show gemma3:1b` and check the Capabilities section. |
| 8 | If a model can't do native tool calls, do we refuse tools (fail closed) or parse JSON from its text? | Month 3 | Mentor recommendation: fail closed. Parsing model text is a security risk. |
| 9 | Can the app detect that it reached the wrong Ollama (WSL vs. Windows, both on port 11434)? | Month 1 Week 3 | A clear "model not found" error is the first defence. |
| 10 | Is the `>=3.11` floor actually tested? | Month 6 Week 2 (CI) | [ADR 0001](decisions/0001-python-version.md). |
| 11 | Should dependencies move into `pyproject.toml`, and should versions be pinned? | Month 6 Week 2 | [ADR 0002](decisions/0002-venv-requirements.md). |

## Assumptions we are relying on

- Ollama v0.40.11 exposes `/api/chat`, which accepts a list of role/content messages (matches `list[Message]`). Verify in Week 3.
- `gemma3:4b` is fast enough on the Dynabook for development (32GB RAM, no real GPU).

## Closed

| # | Question | Decided in |
|---|---|---|
| 1 | What should `generate()` return: `str` or a result object? | [ADR 0008](decisions/0008-reply-object.md): `Reply(text, stop_reason, usage)` |
| 2 | One `ProviderError` or a hierarchy? Does the factory's "not implemented" share it? | [ADR 0009](decisions/0009-provider-error-hierarchy.md): three subclasses by caller action; factory raises the setup type |
| 3 | Where do timeouts and retries live? | Decided 2026-10-26 (no ADR): one `RetryingProvider` wrapper retries `ProviderTemporaryError` once; adapters and CLI never retry. Timeout seconds come from `Settings` (per laptop). Tool actions are never auto-retried. |
