# Open design questions

Unresolved questions and assumptions to revisit. Each one has the trigger that should reopen it. When a question is decided, write an ADR and move it to the "Closed" section with a link.

| # | Question | Trigger to decide | Notes |
|---|---|---|---|
| 4 | Streaming: how will partial replies reach the CLI, and how do errors mid-stream behave? | Month 2 Week 2 | Matters most on the 4GB Dell. |
| 7a | Which local model do we use for tools, if any? | Before Month 3 | Follow-up to closed #7: gemma3 has no tools capability. Options: a different local model that lists `tools` in `ollama show`, or tools only via OpenRouter. |
| 8 | If a model can't do native tool calls, do we refuse tools (fail closed) or parse JSON from its text? | Month 3 | Mentor recommendation: fail closed. Parsing model text is a security risk. Now a live question for local models, because gemma3 has no tools capability (closed #7). |
| 9 | Can the app detect that it reached the wrong Ollama (WSL vs. Windows, both on port 11434)? | Month 1 Week 3 | A clear "model not found" error is the first defence. Partly mitigated in Block 3 (2026-11-19): the adapter reports a missing model with the exact `ollama pull` fix. Still open: the app cannot tell WHICH Ollama it reached. |
| 10 | Is the `>=3.11` floor actually tested? | Month 6 Week 2 (CI) | [ADR 0001](decisions/0001-python-version.md). |
| 11 | Should dependencies move into `pyproject.toml`, and should versions be pinned? | Month 6 Week 2 | [ADR 0002](decisions/0002-venv-requirements.md). |
| 13 | How do we know a change made W.I.N.T.E.R better, not just different? An evaluation habit: a small fixed set of test prompts run against the mock and a real model. | First small set Month 2; real use at the Month 6 checkpoint | Gap found 2026-10-26. No evaluation is planned in the design yet. Keep the set tiny, free of real personal data, and with fixed expected properties (not exact wording). |
| 14 | Retry experience and first-call timeout: should the user see "slow, trying once more..." before the retry, and does the first call to a model need a longer timeout? | Month 1 Week 3 (measure on the Dynabook) | Follow-up to [ADR 0010](decisions/0010-timeouts-and-retries.md), which does not cover it. Worst case the user waits about 2 x the timeout in silence. The first call loads the model into RAM. **Measured 2026-11-19 on the Dynabook:** the first call to `gemma3:4b` took 5.6 s (cold) and 0.6 s (warm), so the 120 s default timeout is very generous there. Not yet measured on the 4GB Dell, where a cold start is likely much slower. Believed, not verified: Ollama keeps loading after the client times out, so the retry often succeeds. A rate-limit retry (OpenRouter) probably needs a short wait first. |
| 15 | Should old messages be summarised instead of just dropped? | After the Month 2 Week 2 cost and latency measurements; again at Month 5 (memory) | Follow-up to [ADR 0012](decisions/0012-conversation-ownership-and-history-limit.md), which drops the oldest exchanges visibly in version 1. Costs: an extra model call per trim, a small model can distort facts, and the summary is untrusted model output. Needs the trimming logic first. |
| 16 | When does the system prompt move from a plain text file with `string.Template` to Jinja2? | Month 3, when a prompt needs conditions or loops (for example listing the available tools) | Follow-up to ADR 0012. Jinja2 is a new dependency and a template engine runs logic, so only values we supply may enter a template; conversation text never does. Write a short ADR when adopting it. |

## Assumptions we are relying on

- Ollama v0.40.11 exposes `/api/chat`, which accepts a list of role/content messages (matches `list[Message]`). Verified 2026-11-19 (Block 3).
- `gemma3:4b` is fast enough on the Dynabook for development (32GB RAM, no real GPU).
- Ollama runs on the CPU here (Intel integrated graphics only). Verified 2026-11-19: `ollama ps` shows `100% CPU` for `gemma3:4b`.
- Ollama's `/api/chat` honors `options.num_ctx` to set the context window. Verified 2026-11-20 by experiment (`ollama ps` showed CONTEXT 8192 and all 7,426 tokens were read); see [ADR 0012](decisions/0012-conversation-ownership-and-history-limit.md).

## Closed

| # | Question | Decided in |
|---|---|---|
| 1 | What should `generate()` return: `str` or a result object? | [ADR 0008](decisions/0008-reply-object.md): `Reply(text, stop_reason, usage)` |
| 2 | One `ProviderError` or a hierarchy? Does the factory's "not implemented" share it? | [ADR 0009](decisions/0009-provider-error-hierarchy.md): three subclasses by caller action; factory raises the setup type |
| 7 | Does gemma3 support tool calling in Ollama? | Verified 2026-10-26 with `ollama show` (Ollama v0.40.11): **No.** `gemma3:4b` lists `completion` and `vision`; `gemma3:1b` lists `completion` only. Neither lists `tools`. A fact, not a decision, so no ADR. Follow-ups: open #7a and #8; revisit [ADR 0004](decisions/0004-ollama-first.md) if Month 3 needs another model. |
| 12 | Context window and history size: how is a growing history kept within the model's context limit? | [ADR 0012](decisions/0012-conversation-ownership-and-history-limit.md), implemented 2026-11-20. Verified by experiment: Ollama's default window is 4096 tokens and it drops old messages silently (HTTP 200, no warning). Now: `LOCAL_AI_CONTEXT_TOKENS` sets one window used for our budget and for Ollama's `num_ctx`; `Session.trim()` drops the oldest whole exchanges and the CLI shows a `[note]`. Follow-ups: 15 (summarise), and the unverified claim that trimming in chunks keeps Ollama's reuse of the conversation start (check in Month 2 Week 2). |
| 6 | Who owns conversation history and the system prompt? | [ADR 0012](decisions/0012-conversation-ownership-and-history-limit.md) (2026-11-20): a small session object owns the messages and the system prompt; interfaces use it; a future orchestrator would use it too. |
| 5 | Which model is used, `model_low` or `model_high`? Who decides? | Block 2b-3 (2026-11-19): the user decides in `.env` with `LOCAL_AI_MODEL_TIER=low\|high` (default `low`, the safe choice for small laptops); `Settings.model` returns the chosen name and adapters use only that. Small decision, recorded here instead of an ADR. Revisit if automatic routing by question difficulty is wanted (Month 2 or later). |
| 3 | Where do timeouts and retries live? | [ADR 0010](decisions/0010-timeouts-and-retries.md): one `RetryingProvider` wrapper retries `ProviderTemporaryError` once; adapters and CLI never retry. Timeout seconds come from `Settings` (per laptop). Tool actions are never auto-retried. |
