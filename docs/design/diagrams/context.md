# Context diagram

W.I.N.T.E.R and the things outside it, **as built on 2026-10-26**. Dashed lines are planned, not built.

```mermaid
flowchart LR
    user([Sridhar]) -- types --> winter[W.I.N.T.E.R CLI]
    winter -- prints --> user
    env[(.env and environment variables)] -- read once at startup --> winter
    winter -. HTTP localhost:11434, Month 1 Week 3 .-> ollama[Ollama on Windows]
    winter -. HTTPS + API key, after Ollama .-> openrouter[OpenRouter]
```

## Notes

- Only the CLI and the mock provider exist today. No network calls are made yet.
- Ollama runs natively on Windows. The old WSL Ollama also uses port 11434; keep it stopped (see [ADR 0004](../decisions/0004-ollama-first.md)).
