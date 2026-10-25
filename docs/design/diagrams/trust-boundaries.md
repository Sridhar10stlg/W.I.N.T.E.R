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

## Planned, not built yet

- **Safe terminal output.** Reply text is untrusted and can carry terminal control characters (escape sequences that move the cursor, change colours or rewrite earlier lines). Before the CLI prints `Reply.text`, a small helper should strip them, keeping normal text, newlines and tabs. The model's words are still shown; only control codes are removed. To be added with the `Reply` work ([ADR 0008](../decisions/0008-reply-object.md)); needs a test that an escape sequence in a reply does not reach the output. Stored history should keep the original text or the cleaned text consistently; decide in the code session.
