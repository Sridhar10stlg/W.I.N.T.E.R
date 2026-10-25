# Open design questions

Unresolved questions and assumptions to revisit. Each one has the trigger that should reopen it. When a question is decided, write an ADR and move it to the "Closed" section with a link.

| # | Question | Trigger to decide | Notes |
|---|---|---|---|
| 4 | Streaming: how will partial replies reach the CLI, and how do errors mid-stream behave? | Month 2 Week 2 | Matters most on the 4GB Dell. |
| 5 | Which model is used, `model_low` or `model_high`? Who decides? | Month 1 Week 3 | Both exist in `Settings`; nothing chooses between them. |
| 6 | Who owns conversation history and the system prompt: the CLI, a session object, or an orchestrator? | Month 2 Week 1 | Mentoring topic 2. Today `run_chat` owns it ([ADR 0007](decisions/0007-cli-structure.md)). |
| 7a | Which local model do we use for tools, if any? | Before Month 3 | Follow-up to closed #7: gemma3 has no tools capability. Options: a different local model that lists `tools` in `ollama show`, or tools only via OpenRouter. |
| 8 | If a model can't do native tool calls, do we refuse tools (fail closed) or parse JSON from its text? | Month 3 | Mentor recommendation: fail closed. Parsing model text is a security risk. Now a live question for local models, because gemma3 has no tools capability (closed #7). |
| 9 | Can the app detect that it reached the wrong Ollama (WSL vs. Windows, both on port 11434)? | Month 1 Week 3 | A clear "model not found" error is the first defence. |
| 10 | Is the `>=3.11` floor actually tested? | Month 6 Week 2 (CI) | [ADR 0001](decisions/0001-python-version.md). |
| 11 | Should dependencies move into `pyproject.toml`, and should versions be pinned? | Month 6 Week 2 | [ADR 0002](decisions/0002-venv-requirements.md). |
| 12 | Context window and history size: how is a growing history kept within the model's context limit, and who decides what to drop or summarize? | Month 2 Week 1 (with #6) | Gap found 2026-10-26. History grows every turn. Believed, not verified: Ollama's runtime default context size is much smaller than the model's maximum (`ollama show` lists 131072 for `gemma3:4b` and 32768 for `gemma3:1b`, but that is the model's limit, not the server's default) and it may silently drop older messages, so a long chat would "forget" without any error. Check the actual default and behaviour in Week 3. Decide: a token budget, a visible warning, and whether the adapter sets the context size. |
| 13 | How do we know a change made W.I.N.T.E.R better, not just different? An evaluation habit: a small fixed set of test prompts run against the mock and a real model. | First small set Month 2; real use at the Month 6 checkpoint | Gap found 2026-10-26. No evaluation is planned in the design yet. Keep the set tiny, free of real personal data, and with fixed expected properties (not exact wording). |
| 14 | Retry experience and first-call timeout: should the user see "slow, trying once more..." before the retry, and does the first call to a model need a longer timeout? | Month 1 Week 3 (measure on the Dynabook) | Follow-up to [ADR 0010](decisions/0010-timeouts-and-retries.md), which does not cover it. Worst case the user waits about 2 x the timeout in silence. The first call loads the model into RAM (about 20 to 60 seconds, a rough estimate). Believed, not verified: Ollama keeps loading after the client times out, so the retry often succeeds. A rate-limit retry (OpenRouter) probably needs a short wait first. |

## Assumptions we are relying on

- Ollama v0.40.11 exposes `/api/chat`, which accepts a list of role/content messages (matches `list[Message]`). Verify in Week 3.
- `gemma3:4b` is fast enough on the Dynabook for development (32GB RAM, no real GPU).
- Ollama runs on the CPU here (Intel integrated graphics only). Not verified; check with `ollama ps` while a model is loaded (see the PROCESSOR column).

## Closed

| # | Question | Decided in |
|---|---|---|
| 1 | What should `generate()` return: `str` or a result object? | [ADR 0008](decisions/0008-reply-object.md): `Reply(text, stop_reason, usage)` |
| 2 | One `ProviderError` or a hierarchy? Does the factory's "not implemented" share it? | [ADR 0009](decisions/0009-provider-error-hierarchy.md): three subclasses by caller action; factory raises the setup type |
| 7 | Does gemma3 support tool calling in Ollama? | Verified 2026-10-26 with `ollama show` (Ollama v0.40.11): **No.** `gemma3:4b` lists `completion` and `vision`; `gemma3:1b` lists `completion` only. Neither lists `tools`. A fact, not a decision, so no ADR. Follow-ups: open #7a and #8; revisit [ADR 0004](decisions/0004-ollama-first.md) if Month 3 needs another model. |
| 3 | Where do timeouts and retries live? | [ADR 0010](decisions/0010-timeouts-and-retries.md): one `RetryingProvider` wrapper retries `ProviderTemporaryError` once; adapters and CLI never retry. Timeout seconds come from `Settings` (per laptop). Tool actions are never auto-retried. |
