# GitHub Workflow for W.I.N.T.E.R

This repository is maintained by one developer. GitHub should provide clarity and history without imposing team-sized process overhead.

## 1. Account and repository

- Keep the primary repository in the personal GitHub account.
- Start with a **private repository** while architecture and personal integrations are evolving.
- Use a clear name such as `winter-ai`.
- A second account is not required to work on the same repository. Configure Git identity deliberately if you use different identities on different machines.
- Do not copy employer-owned code, customer data, internal documentation, or credentials into this personal repository. Check employer policies before using work equipment or work time.
- Make the repository public only after checking the license, secrets, personal data, dependencies, and employer/IP constraints.

## 2. Create the repository

On GitHub:
1. Select **New repository**.
2. Name it `winter-ai`.
3. Choose **Private**.
4. Add a README.
5. Add a Python `.gitignore`.
6. Choose a license only when you have decided how others may use the code. A private project does not need an immediate license decision.
7. Create the repository.

## 3. Create a GitHub Project

Recommended starting choice: **Board**.

Suggested columns:
- **To do**
- **In progress**
- **Done**

Start with one project board. Add a roadmap or additional views only when they solve a real planning problem.

Useful fields:
- **Status:** To do / In progress / Done
- **Priority:** High / Medium / Low
- **Phase:** Foundation / Text assistant / Tools / Voice / Memory / Integrations / Local AI / Vision / Reliability
- **Type:** Feature / Bug / Research / Documentation / Security

Keep no more than one or two issues actively in progress. The board is a personal focus tool, not a report for a manager.

## 4. Issues and milestones

Create an issue for each meaningful task. Keep issues small enough to finish in one or a few sessions.

### Suggested labels

- `feature`
- `bug`
- `research`
- `architecture`
- `security`
- `documentation`
- `good-first-task` (optional; useful if you later invite contributors)
- `phase-1`, `phase-2`, etc.
- `priority: high`, `priority: medium`, `priority: low`

### Suggested milestones

1. **Phase 0 — Foundation**
2. **Phase 1 — Text-first assistant**
3. **Phase 2 — Tools and controlled execution**
4. **Phase 3 — Voice**
5. **Phase 4 — Memory**
6. **Phase 5 — Integrations**
7. **Phase 6 — Local AI**
8. **Phase 7 — Vision and devices**
9. **Phase 8 — Reliability**
10. **Phase 9 — Advanced interfaces**

Milestones describe outcomes, not rigid deadlines.

### Issue template

```markdown
## Goal
What outcome should this task achieve?

## Context
Why is it needed? Link related issues or notes.

## Acceptance criteria
- [ ] Observable result 1
- [ ] Observable result 2
- [ ] Tests or validation added

## Safety / privacy considerations
Does this touch credentials, personal data, files, external services, or devices?

## Notes
Options considered, open questions, and implementation notes.
```

## 5. Branches, commits, and pull requests

For small solo changes, committing directly to `main` can work, but use short-lived branches for meaningful features, security-sensitive changes, and experiments you may want to review.

Suggested branch names:
- `feat/voice-input`
- `feat/tool-registry`
- `fix/config-validation`
- `docs/architecture`
- `research/local-models`

Suggested commit style:
- `feat: add calculator tool`
- `fix: validate missing API key`
- `docs: describe memory policy`
- `test: cover tool argument validation`
- `refactor: isolate model provider`

Use pull requests when a change is substantial, when you want a review checkpoint, or when automated checks should run before merging. Self-review is still valuable.

## 6. Security and repository settings

- Never commit `.env`, API keys, access tokens, private keys, passwords, or real user data.
- Commit `.env.example` with placeholder values only.
- Enable GitHub secret scanning and push protection if available for the repository and plan.
- Use dependency update/security alerts where available.
- Use least-privilege tokens and remove unused credentials.
- If a secret is committed, revoke/rotate it immediately. Deleting it from the latest commit is not enough because Git history may retain it.
- Avoid logging full prompts, tool arguments, document contents, or personal data by default.
- Keep automated workflows on minimal permissions; pin third-party actions appropriately and review workflow changes.
- Do not grant the assistant unrestricted repository, shell, or account access.

## 7. Recommended files

- `README.md` — project overview and quick start.
- `PLAN.md` — vision, architecture, phases, security, and hardware strategy.
- `GITHUB.md` — this workflow.
- `CLAUDE.md` — coding-agent instructions for Claude Code or compatible workflows.
- `.gitignore` — ignore virtual environments, caches, `.env`, local data, and generated files.
- `.env.example` — names of required settings with placeholder values.
- `pyproject.toml` — dependencies and tooling.
- `docs/architecture.md` — architecture detail once it stabilizes.
- `docs/security.md` — permission model and threat considerations.
- `docs/decisions/` — short architecture decision records.

Use one naming convention consistently. The requested filenames `GitHub.md` and `claude.md` are valid, but `GITHUB.md` and `CLAUDE.md` are common all-caps conventions. On case-sensitive systems, filenames are case-sensitive.

## 8. Suggested first board items

1. Create repository and baseline documentation.
2. Add Python project configuration and `.gitignore`.
3. Add validated configuration and `.env.example`.
4. Create CLI skeleton.
5. Define model-provider interface.
6. Add mocked provider tests.
7. Add first real provider adapter.
8. Add structured logging and secret redaction.
9. Add a tool registry with schema validation.
10. Document permissions and human confirmation rules.

## 9. Weekly solo workflow

1. Pick one outcome for the week.
2. Break it into small issues with acceptance criteria.
3. Move only the current task to **In progress**.
4. Commit in small, understandable changes.
5. Run tests before marking an issue done.
6. Add notes for decisions or failed experiments so research is not repeated.
7. Revisit the backlog periodically and close ideas that no longer matter.

**Rule of thumb:** GitHub should make the next step obvious. If maintaining the board becomes more work than building W.I.N.T.E.R, simplify it.
