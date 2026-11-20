# Request flow

How one chat turn travels through the code, **as built on 2026-11-20** (after Month 2 Week 1).

## Startup

```text
main()
  ├─ load_settings()      bad value       → print field + reason (never the value) → exit 2
  ├─ build_provider()     ProviderSetupError (e.g. no adapter yet, bad URL) → "[error] ..." → exit 2
  │                       returns RetryingProvider(inner provider)
  ├─ Session(load_system_prompt(), budget_tokens=prompt_budget(context_tokens))
  └─ run_chat(provider, session)                                                   → exit 0
```

Exit 1 is not used by `main()`. Python itself uses it for an uncaught exception (a bug, fail loud).

## One turn

```mermaid
sequenceDiagram
    participant U as User
    participant C as run_chat
    participant S as Session
    participant P as RetryingProvider (wraps Ollama or the mock)
    U->>C: line of text
    C->>S: add_user(text)
    C->>S: trim()
    alt message too long even for an empty chat
        S-->>C: ConversationTooLongError
        C->>S: discard_last_user()
        C->>U: [error] too long
    else fits (after trimming if needed)
        S-->>C: number of dropped messages
        opt dropped more than 0
            C->>U: [note] N older messages were dropped
        end
        C->>S: messages_for_model()
        S-->>C: system prompt + history (a new list)
        C->>P: generate(messages)
        Note over P: a ProviderTemporaryError is retried once here, nowhere else
        alt reply
            P-->>C: Reply(text, stop_reason, usage)
            C->>S: add_assistant(reply.text)
            C->>U: winter> reply.text (cleaned for the terminal)
        else ProviderError
            P-->>C: ProviderError
            C->>S: discard_last_user()
            C->>U: [error] message
        end
    end
```

## Notes

- The `Session` owns the conversation ([ADR 0012](../decisions/0012-conversation-ownership-and-history-limit.md)): the system prompt and the user/assistant history, always in whole question-and-answer pairs.
- `trim()` keeps, in priority order: the system prompt, the newest message, the first exchange (if it fits), the most recent exchanges. It drops the rest from the middle in whole pairs, down to about 75% of the budget. Trimming is permanent.
- The budget is the context window (`LOCAL_AI_CONTEXT_TOKENS`) minus a 512-token reply reserve. The same window is sent to Ollama as `num_ctx`.
- The system prompt comes from a file; conversation text is never rendered into it.
- Any exception other than `ProviderError` and `ConversationTooLongError` is not caught and shows a traceback on purpose.
