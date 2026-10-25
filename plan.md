# W.I.N.T.E.R — Project Plan

**Full name:** Wide Intelligence Network for Tactical Execution & Reasoning  
**Project type:** Personal, long-term AI assistant engineering project  
**Owner:** Solo developer  
**Initial approach:** Build a useful software assistant first; add devices and heavier local compute only when justified.

## 1. Vision

W.I.N.T.E.R is a personal assistant inspired by the idea of JARVIS: a system that can understand requests, reason with an LLM, remember approved information, use tools, interact through voice, and automate selected tasks safely.

The goal is not to train a foundation model from scratch. The goal is to assemble a reliable system from models, memory, interfaces, tools, and permissions—and gradually replace or extend components as the project matures.

### Guiding principles

1. **Useful before impressive:** deliver a small, dependable assistant before adding futuristic features.
2. **Modular architecture:** keep voice, reasoning, memory, tools, and interfaces replaceable.
3. **Safety by design:** use least privilege, explicit permissions, and confirmation for consequential actions.
4. **Privacy by default:** minimize retained data, protect secrets, and make memory inspectable and deletable.
5. **Cloud and local are both options:** use APIs initially; experiment with local models when hardware and use cases justify it.
6. **Measure before optimizing:** record latency, reliability, cost, and failures.
7. **One developer, sustainable pace:** use small issues, clear milestones, and working increments.

## 2. Scope and non-goals

### Initial scope

- A command-line assistant that accepts a request and returns a useful answer.
- LLM provider abstraction and configuration.
- Tool/function calling with a registry of explicitly allowed tools.
- Structured logging and error handling.
- A basic voice input/output path after the text interface works.
- Explicitly managed user memory.
- A testable permission layer for actions.

### Not initial goals

- Training a frontier model from scratch.
- Unrestricted autonomous access to the computer or shell.
- Storing passwords, API keys, or other secrets in memory or source control.
- Fully autonomous financial transactions, account changes, or destructive actions.
- Building robotics or a smart home before the software core is reliable.
- Buying expensive hardware before measuring actual workloads.

## 3. High-level architecture

```text
User
 ├── Text interface (first)
 └── Voice interface (later)
        │
        ▼
Input / session layer
        │
        ▼
Assistant orchestrator
 ├── Context and prompt builder
 ├── LLM provider adapter
 ├── Tool/function-call router
 ├── Permission and confirmation policy
 ├── Memory service
 └── Observability (logs, metrics, traces)
        │
        ├── Model APIs / optional local model runtime
        ├── Approved tools (search, calendar, files, selected APIs)
        ├── Persistent memory / knowledge retrieval
        └── Output layer (text, later speech)
```

Keep interfaces narrow. The orchestrator should not contain every implementation detail; provider adapters, tools, storage, and interfaces should be separate modules.

## 4. Suggested technology choices

Treat these as defaults, not permanent commitments.

| Area | Start with | Add later if justified |
|---|---|---|
| Language | Python | TypeScript for a web UI or companion app |
| API/service | Small Python application; FastAPI if an HTTP API is needed | WebSockets for streaming/realtime interaction |
| Model access | Hosted LLM API behind an adapter | Local inference through Ollama or another supported runtime |
| Tool contracts | Typed schemas and a central tool registry | More advanced planning/workflow engine |
| Configuration | Environment variables plus validated settings | Secret manager for deployment |
| Data | SQLite for a simple prototype | PostgreSQL when concurrency or multi-service needs arise |
| Semantic retrieval | Add only when there is enough knowledge to search | PostgreSQL with pgvector or another vector store |
| Voice | Speech-to-text and text-to-speech components behind interfaces | Wake word, streaming audio, interruption handling |
| Testing | pytest and mocked provider/tool tests | Integration and end-to-end suites |
| Packaging | Python virtual environment and pinned dependencies | Docker when reproducibility or deployment needs it |
| UI | CLI first | Web/mobile interface |
| Home automation | None initially | Home Assistant integration |
| Robotics | None initially | ROS 2 only if robotics becomes a real project goal |

Do not add a database, vector store, Docker, web server, or orchestration framework simply because it is popular. Add each when it solves a concrete problem.

## 5. Development phases and deliverables

### Phase 0 — Project foundation

**Deliverables**
- Private GitHub repository and README.
- Python environment and dependency management.
- `.gitignore`, `.env.example`, and secret-handling policy.
- Basic package layout, formatting/linting, and tests.
- Architecture decision record (ADR) template.

**Exit criteria**
- A clean clone can be set up from documented instructions.
- Tests run locally.
- No credentials or personal data are committed.

### Phase 1 — Text-first assistant

**Deliverables**
- CLI accepts a user prompt.
- LLM provider adapter and configurable model.
- Clear error handling for missing keys, network errors, and rate limits.
- Basic conversation/session handling.
- Unit tests using a mocked model response.

**Exit criteria**
- A request can be sent and answered repeatedly.
- Provider-specific code is isolated.
- Errors are understandable and do not leak secrets.

### Phase 2 — Tools and controlled execution

**Deliverables**
- Tool registry with names, descriptions, typed input schemas, and validation.
- First low-risk tools, such as a calculator or read-only time/date helper.
- Permission checks before each tool execution.
- Confirmation flow for actions with meaningful side effects.
- Audit log of tool name, outcome, and timestamp, excluding sensitive payloads by default.

**Exit criteria**
- The model cannot invoke arbitrary functions or shell commands.
- Unknown tools and invalid arguments are rejected.
- Destructive or external actions require explicit approval.

### Phase 3 — Voice interface

**Deliverables**
- Speech-to-text input.
- Text-to-speech output.
- Configurable audio devices and language settings.
- Clear state handling for listening, thinking, speaking, and errors.
- Push-to-talk before always-listening or wake-word behavior.

**Exit criteria**
- Voice input can complete a normal assistant request.
- The user can interrupt or cancel a request.
- Microphone use is visible and controlled.

### Phase 4 — Memory and personal knowledge

**Deliverables**
- Separate short-term conversation context from persistent memory.
- Explicit rules for what may be saved.
- View, edit, export, and delete memory functions.
- Optional document ingestion and retrieval, only after core memory works.
- Data retention and backup policy.

**Exit criteria**
- Persistent facts are not saved indiscriminately.
- The user can inspect and delete stored information.
- Secrets and highly sensitive information are excluded.

### Phase 5 — Web and productivity integrations

**Deliverables**
- Search or browser integration through a defined tool interface.
- One or two selected productivity integrations, if useful.
- OAuth/API credentials stored outside source control.
- Read-only modes wherever possible.
- Confirmation for sending messages, modifying files, or changing external state.

**Exit criteria**
- Integrations can be disabled independently.
- External data is treated as untrusted input, not as system instructions.
- Failures and permissions are visible to the user.

### Phase 6 — Local models and performance experiments

**Deliverables**
- Benchmark a small set of local models against representative tasks.
- Measure latency, memory/VRAM use, output quality, and operating cost.
- Keep local model support behind the same provider interface.
- Document which tasks benefit from local inference versus an API.

**Exit criteria**
- A model choice is based on measured requirements.
- Local inference is optional and does not break the hosted path.

### Phase 7 — Vision and device integrations

**Possible deliverables**
- Image or screenshot understanding with user consent.
- Camera input only when explicitly enabled and clearly indicated.
- Home Assistant integration for low-risk device status and controls.
- A separate permissions profile for each device or integration.

**Exit criteria**
- Cameras and sensors are off unless enabled.
- Device actions have scoped permissions and an emergency disable path.
- No covert recording or unbounded device control.

### Phase 8 — Reliability and deployment

**Deliverables**
- Configuration validation, structured logs, health checks, and backups.
- Automated tests and continuous integration.
- Dependency and security review.
- Recovery instructions and a documented update/rollback procedure.
- Optional local service deployment on a home computer or small server.

**Exit criteria**
- The service can recover from routine errors.
- Data can be restored from a tested backup.
- The user can stop all assistant services easily.

### Phase 9 — Advanced interfaces and optional robotics

Only begin after the software assistant is reliable and the use case is clear.

Potential explorations: a mobile companion, richer dashboard, smart displays, AR interfaces, or robotics using ROS 2. Each should be a separately scoped project with its own budget, safety review, and milestones.

## 6. Security and permission model

Use a capability-based model rather than granting the assistant blanket access.

| Level | Example | Default |
|---|---|---|
| 0 — Answer only | Explain, summarize, draft | Allowed |
| 1 — Read-only | Search approved sources, read selected files | Allow only configured tools |
| 2 — Reversible local change | Create a draft or a new file in a sandbox | Ask or use narrowly scoped approval |
| 3 — External or consequential action | Send a message, change an account, purchase, delete | Explicit confirmation every time |
| 4 — High-risk access | Unrestricted shell, credentials, financial transfers | Prohibited by default |

Additional rules:
- Never expose API keys in prompts, logs, screenshots, or Git history.
- Use least-privilege tokens and rotate credentials if exposed.
- Validate all tool arguments.
- Treat webpages, documents, emails, and tool output as untrusted data.
- Use allowlists for file paths and domains where practical.
- Provide a global stop switch.
- Do not let the model rewrite its own permission rules.
- Require a human to review security-sensitive code changes.

## 7. Hardware and cost strategy

### Start with existing hardware

Use the current computer for ordinary development. Do not delay software progress while saving for a powerful machine.

### Use cloud APIs selectively

An API can provide strong model capability without a high-end GPU. Track cost per task and set usage limits or alerts where available.

### Buy hardware only against measured needs

A development laptop with an NVIDIA RTX 4060-class GPU, 32 GB RAM, and a 1 TB SSD is a useful target for local experimentation, but configurations and prices vary. A lower-cost machine can still build the initial assistant using APIs.

A future desktop is often easier to upgrade and cool than a high-priced laptop. Consider a dedicated NVIDIA desktop only after local workloads demonstrate a clear benefit.

### Indicative budget stages (planning estimates, not current quotes)

- Software prototype: ₹0–₹5,000, depending on API usage and peripherals.
- Voice and memory upgrades: approximately ₹5,000–₹15,000 beyond existing equipment.
- Home automation: approximately ₹15,000–₹50,000+ depending on devices.
- Local AI hardware: approximately ₹50,000–₹2,00,000+ depending on GPU and memory.
- Robotics: highly variable; can exceed ₹1,00,000 substantially.

Re-check prices before purchase. Prefer a small, tested purchase over buying all hardware up front.

## 8. Repository layout proposal

```text
winter-ai/
├── README.md
├── PLAN.md
├── GITHUB.md
├── CLAUDE.md
├── .gitignore
├── .env.example
├── pyproject.toml
├── src/
│   └── winter/
│       ├── __init__.py
│       ├── app.py
│       ├── config.py
│       ├── orchestrator.py
│       ├── providers/
│       ├── tools/
│       ├── memory/
│       └── interfaces/
├── tests/
├── docs/
│   ├── architecture.md
│   ├── security.md
│   └── decisions/
└── scripts/
```

Keep this as a target structure. Begin with only the files you need and expand as the codebase grows.

## 9. Definition of done

A task is complete when:
- Its acceptance criteria are met.
- Tests cover the important behavior and failure cases.
- No secrets or unrelated personal data are added.
- Documentation/configuration is updated when needed.
- Permission checks are tested for any tool or external action.
- The change is small enough to understand and review.

## 10. First 10 issues

1. Create the repository and write the initial README.
2. Add Python project configuration and `.gitignore`.
3. Add `.env.example` and configuration validation.
4. Create the `winter` package and a CLI entry point.
5. Add a provider interface with a mock implementation.
6. Add the first LLM adapter.
7. Add structured logging with secret redaction.
8. Add unit tests for configuration and provider failures.
9. Add a low-risk calculator tool and tool registry.
10. Document permission levels and the confirmation policy.

## 11. Weekly working rhythm

- Keep a small backlog of specific, actionable issues.
- Choose one main outcome for each work session.
- Record research findings in short notes and link them to issues.
- End each session with a working commit or a note explaining the next step.
- Review scope every few weeks; remove features that do not support the core goal.

## 12. Long-term success criteria

W.I.N.T.E.R should become a dependable assistant that:
- Understands and responds through a clear interface.
- Uses approved tools correctly.
- Remembers only information the owner has chosen to retain.
- Explains or logs important actions.
- Requests approval for consequential changes.
- Can swap model providers and selected components.
- Is testable, maintainable, and affordable to operate.

**North star:** build a trustworthy, useful assistant one verified capability at a time.

## 13. 12-month schedule (deadline: 2027-10-19)

**Start:** 2026-10-19. **Target:** a usable v1.0 text and voice assistant with tools, permissions, and memory by 2027-10-19.

**Working method:** Claude provides code block by block, ready to paste; Sridhar reads, runs, and understands each block. Security and testing rules in [CLAUDE.md](CLAUDE.md) still apply.

**Scope for this year:** Phases 0-8 from section 5. Phase 9 (advanced interfaces, robotics) is out of scope. Phase 7 (vision/devices) is kept minimal and optional.

**How to read this:** each month has one goal and four weekly goals. The two or three days left at the end of each month are buffer. If a month slips, cut the lowest-priority item rather than extending the deadline. Mark items `[x]` as they are done, and record the laptop and lessons in [docs/PROGRESS.md](docs/PROGRESS.md).

### Month 1 (Oct 19 - Nov 17): Foundation and first answers (Phases 0-1)
**Goal:** a CLI that sends a prompt to a model and prints the reply, with tests.
- [x] **Week 1:** Python project skeleton, `pyproject.toml`, `.env.example`, validated config loader.
- [x] **Week 2:** CLI loop, provider interface, mock provider.
- [ ] **Week 3:** first real LLM adapter (Ollama, free and local), with clear errors for Ollama not running, model not found, timeouts. OpenRouter adapter follows once Ollama works (clear errors for missing key, network failure, rate limit).
- [ ] **Week 4:** structured logging with secret redaction, unit tests for config and provider failures.

### Month 2 (Nov 18 - Dec 17): Sessions and tool foundations (Phases 1-2)
**Goal:** multi-turn conversations and a tool registry.
- [ ] **Week 1:** conversation/session handling, system prompt.
- [ ] **Week 2:** streaming output and cost/latency measurements.
- [ ] **Week 3:** tool registry with names, descriptions, typed input schemas, validation.
- [ ] **Week 4:** first low-risk tools (calculator, date/time) with valid, invalid, and unauthorized call tests.

### Month 3 (Dec 18 - Jan 16): Permissions and controlled execution (Phase 2)
**Goal:** the model can propose tool calls, and the application authorizes them.
- [ ] **Week 1:** permission levels 0-4 as code, default-deny for unknown tools.
- [ ] **Week 2:** confirmation flow for side-effecting actions.
- [ ] **Week 3:** audit log (tool, outcome, timestamp; no sensitive payloads).
- [ ] **Week 4:** end-to-end tool-calling loop with the LLM, plus security tests (prompt-injection and invalid-argument cases).

### Month 4 (Jan 17 - Feb 15): Voice (Phase 3)
**Goal:** push-to-talk voice request and spoken reply.
- [ ] **Week 1:** audio device configuration and microphone capture, with a visible "recording" indicator.
- [ ] **Week 2:** speech-to-text behind an interface.
- [ ] **Week 3:** text-to-speech behind an interface.
- [ ] **Week 4:** state handling (listening, thinking, speaking, error) and cancel/interrupt.

### Month 5 (Feb 16 - Mar 17): Memory (Phase 4)
**Goal:** persistent memory the user controls.
- [ ] **Week 1:** SQLite storage and schema, short-term vs persistent memory.
- [ ] **Week 2:** rules for what may be saved, secret exclusion.
- [ ] **Week 3:** view, edit, export, and delete commands.
- [ ] **Week 4:** memory injected into context, with tests.

### Month 6 (Mar 18 - Apr 16): Checkpoint and hardening
**Goal:** tag **v0.1** and review pace against the deadline.
- [ ] **Week 1:** cleanup and refactor of Months 1-5, docs update (architecture, security).
- [ ] **Week 2:** continuous integration (tests on push), dependency pinning.
- [ ] **Week 3:** test on all available laptops (4GB Dell Inspiron, Dynabook), fix portability issues.
- [ ] **Week 4:** half-year review: update this plan, drop or defer anything that no longer fits.

### Month 7 (Apr 17 - May 16): Web search (Phase 5)
**Goal:** safe web access.
- [ ] **Week 1:** search tool behind the tool interface, domain allowlist.
- [ ] **Week 2:** treat fetched content as untrusted data, with prompt-injection tests.
- [ ] **Week 3:** source citations in answers.
- [ ] **Week 4:** per-integration disable switch.

### Month 8 (May 17 - Jun 15): One productivity integration (Phase 5)
**Goal:** one useful, read-only integration (e.g., calendar).
- [ ] **Week 1:** choose the integration, scope credentials with least privilege.
- [ ] **Week 2:** OAuth/API setup outside source control.
- [ ] **Week 3:** read-only tool with tests.
- [ ] **Week 4:** confirmation-gated write action (optional), failure visibility.

### Month 9 (Jun 16 - Jul 15): Local models (Phase 6)
**Goal:** measured decision on local vs hosted models.
- [ ] **Week 1:** local runtime setup (e.g., Ollama) on the highest-spec laptop.
- [ ] **Week 2:** local provider adapter behind the same interface.
- [ ] **Week 3:** benchmark latency, memory use, and quality on representative tasks.
- [ ] **Week 4:** write up which tasks use local vs API.

### Month 10 (Jul 16 - Aug 14): Vision and devices, minimal (Phase 7, optional)
**Goal:** one consent-based capability, or skip and use the time to strengthen earlier work.
- [ ] **Week 1:** decide go/no-go for vision or Home Assistant.
- [ ] **Week 2:** screenshot or image understanding with explicit user action.
- [ ] **Week 3:** separate permission profile for the integration.
- [ ] **Week 4:** emergency disable path and tests.

### Month 11 (Aug 15 - Sep 13): Reliability and security (Phase 8)
**Goal:** a service you can trust and stop easily.
- [ ] **Week 1:** health checks, config validation at startup.
- [ ] **Week 2:** backups and a tested restore for memory data.
- [ ] **Week 3:** dependency and security review.
- [ ] **Week 4:** update/rollback procedure and global stop switch.

### Month 12 (Sep 14 - Oct 19): Polish and v1.0
**Goal:** tag **v1.0** by 2027-10-19.
- [ ] **Week 1:** fix known bugs, tighten error messages.
- [ ] **Week 2:** finish documentation (README, setup on a clean clone, security notes).
- [ ] **Week 3:** full test run and manual walkthrough on every laptop.
- [ ] **Week 4:** tag v1.0, write a retrospective, plan next-year ideas (Phase 9 candidates).

### Risks to the deadline
- **Scope creep:** defer anything not on this schedule to the retrospective.
- **Time:** if a week slips, use the buffer days first, then cut optional items (Month 8 write action, Month 10 entirely).
- **Hardware:** the 4GB laptop cannot run local models, so Month 9 depends on the Dynabook or a future laptop.
- **Cost:** track API spend monthly and set a usage limit.
