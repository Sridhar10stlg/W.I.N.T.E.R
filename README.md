# W.I.N.T.E.R

**Wide Intelligence Network for Tactical Execution & Reasoning**

W.I.N.T.E.R is a personal AI-assistant engineering project inspired by the idea of a capable, voice-enabled digital assistant. It aims to combine an LLM, controlled tools, optional memory, voice interfaces, and selected integrations into a modular system that is useful, safe, and maintainable.

> The goal is not to train a foundation model from scratch. The goal is to build a reliable assistant around models, memory, tools, interfaces, and permissions.

## Project status

**Stage:** Foundation built; a text-only CLI chats with a local model (Ollama) or a mock  
**Maintainer:** Solo developer  
**Initial language:** Python  
**Repository visibility:** Private during early development

Working today: configuration, a chat loop, a mock provider, and an Ollama adapter with timeouts, one retry for temporary failures and clear errors. Everything else listed in the roadmap is planned, not implemented. Progress is tracked in [`docs/PROGRESS.md`](docs/PROGRESS.md). This README will be updated as working capabilities are added.

## Vision

Over time, W.I.N.T.E.R may support:
- Text-based assistant interaction.
- LLM provider integrations.
- Explicitly registered tools with validated inputs.
- User-controlled persistent memory and knowledge retrieval.
- Speech-to-text and text-to-speech.
- Approved web and productivity integrations.
- Optional local-model inference.
- Carefully permissioned vision and home-device integrations.

## Guiding principles

- Build useful capabilities incrementally.
- Keep components modular and replaceable.
- Protect secrets and personal data.
- Require confirmation for consequential actions.
- Prefer least privilege and read-only access.
- Test behavior and failure cases.
- Measure local-compute needs before buying hardware.

## Roadmap

1. **Foundation:** repository, Python setup, configuration, logging, tests.
2. **Text-first assistant:** CLI and model-provider adapter.
3. **Tools:** tool registry, schema validation, permissions, confirmations.
4. **Voice:** speech input and spoken output.
5. **Memory:** explicit save/view/edit/delete controls.
6. **Integrations:** selected web and productivity tools.
7. **Local AI:** benchmark hosted and local models.
8. **Vision and devices:** optional, consent-based, scoped integrations.
9. **Reliability:** CI, security review, backups, deployment documentation.
10. **Future exploration:** mobile interface, home automation, or robotics if justified.

See [`PLAN.md`](PLAN.md) for the detailed architecture, phase deliverables, safety model, hardware strategy, and definition of done.

## Getting started

Requires Python 3.11 or newer. The commands below are for Windows PowerShell.

```powershell
# Clone your repository
git clone <your-repository-url>
cd <repository-folder>

# Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install the dependencies, then the package itself in editable mode
pip install -r requirements.txt
pip install -e .

# Copy the example settings and edit your own copy (never commit .env)
Copy-Item .env.example .env

# Run the tests
pytest

# Run the assistant with the fake model (nothing else to install)
$env:LOCAL_AI_PROVIDER = "mock"
python -m winter
Remove-Item Env:LOCAL_AI_PROVIDER
```

To chat with a real local model, install [Ollama](https://ollama.com), then pull a model (`ollama pull gemma3:1b`, or `gemma3:4b` for a laptop with plenty of RAM) and run `python -m winter`. In `.env`, `LOCAL_AI_MODEL_TIER=low` uses the small model and `high` uses the bigger one; `LOCAL_AI_TIMEOUT_SECONDS` sets how long to wait for an answer. Type `/exit` to quit. Do not put real API keys in source files.

## Configuration and secrets

- Keep local credentials in environment variables or an appropriate secret manager.
- Commit `.env.example` with placeholder values only.
- Never commit `.env`, API tokens, passwords, private keys, or personal data.
- Rotate a credential immediately if it is exposed.
- Redact secrets from logs and error messages.

## Safety model

The model may propose actions, but the application must independently validate and authorize them.

- **Answer-only:** normal responses and drafts.
- **Read-only tools:** explicitly configured and scoped.
- **Local changes:** limited to approved paths, with confirmation where appropriate.
- **External or consequential actions:** explicit user confirmation.
- **Unrestricted shell access and high-risk autonomous actions:** disabled by default.

## Repository documents

- [`PLAN.md`](PLAN.md) — detailed project plan and phases.
- [`GITHUB.md`](GITHUB.md) — solo-developer GitHub workflow and project-board recommendations.
- [`CLAUDE.md`](CLAUDE.md) — coding-agent instructions.

## Contributing

This is currently a solo project. If collaboration is opened later, contributions should follow the project’s security, testing, privacy, and documentation expectations. Do not submit secrets or proprietary employer material.

## License

No license has been selected yet. Until a license is added, do not assume that the repository is open for reuse or redistribution.

## North star

Build a trustworthy, useful assistant one verified capability at a time.
