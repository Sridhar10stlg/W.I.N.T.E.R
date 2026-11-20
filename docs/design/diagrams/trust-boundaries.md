# Trust boundaries

What W.I.N.T.E.R trusts and what it treats as untrusted data. A trust boundary is any line where data comes from something the app does not control.

```text
 TRUSTED (our code and decisions)          │  UNTRUSTED (treat as data, never as instructions)
                                           │
  W.I.N.T.E.R code                         │   Model output (text now; tool calls in Month 3)
  Permission policy (Month 3)              │   Web pages, documents, emails (Month 7+)
  Values the app measures itself           │   Tool output (Month 2+)
  (time taken, which model was called)     │
                                           │
 PARTLY TRUSTED (validated before use)     │
  User input from the CLI                  │
  .env and environment variables           │
  (validated by Settings; may hold secrets)│
```

## Rules that follow (from CLAUDE.md and plan.md section 6)

- **Reply text is untrusted too, not just tool calls.** It is shown to the user (it can try to manipulate them), it goes back into history, and later into memory (Month 5) and speech (Month 4). Anything injected into one reply can travel through all of those. In `Reply` ([ADR 0008](../decisions/0008-reply-object.md)), `text` and later `tool_calls` come from the model; `usage` and `stop_reason` come from the provider service, not the model's words.
- The model may **propose**; the app **authorizes**. Model output alone is never proof of permission.
- Never parse model text to find actions to run. Use only structured tool calls, validated against a schema (see [open questions](../open-questions.md)).
- Secrets cross from `.env` into the app only. They must never cross into prompts, logs or error messages.
- Model output must never change the permission policy or these rules.

## As built today

- `Settings` validates config at startup, and `SecretStr` hides the API key.
- Config errors print the field name and reason, never the value.
- There are no tools, so the model can't trigger any action. Its output is only printed.
- **Safe terminal output (Block 2b-1, 2026-11-19):** `safe_for_terminal()` in `cli.py` removes control characters (Unicode category `Cc`, except newline and tab) and bidi controls from reply and error text before printing. **Decided:** clean at the output boundary only; history keeps the raw text, so the model sees exactly what was said. Tested in `tests/test_cli.py`.
- Provider error messages follow the [ADR 0009](../decisions/0009-provider-error-hierarchy.md) rules (no raw response body, no part of a secret). Real adapters must keep to them from Block 3.
- **Ollama adapter (Block 3, 2026-11-19):** the server's reply is treated as untrusted. Its shape is checked at every step, and a broken reply becomes a clean error. Error messages show the HTTP status number only, never the response body. URL credentials are stripped from anything printed, and `LOCAL_OLLAMA_URL` is validated (http or https, host present, numeric port) when the adapter is built, so a bad address stops the app at startup with exit code 2. Tested in `tests/test_ollama.py` with planted canary strings.
