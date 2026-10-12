# W.I.N.T.E.R — Progress Journal

Handoff notes between sessions and laptops. Newest entry first. Sridhar types the code; Claude mentors (see [AI_Guidelines.md](../AI_Guidelines.md)).

---

## 2026-10-12 — Laptop:
- Laptop 1(My personal low spec laptop): Dell Inspiron - 4GB RAM, 256GB SSD, 1TB HDD, Ryzen 3 processor
- Laptop 2(My organization high spec laptop): Dynabook - 32GB RAM, 900GB SSD, Intel I7 255H, 128mb graphics card
- Laptop 3(My new personal laptop high-end): Going to buy
- Laptop 4(My new personal macbook): will buy in 4 years time

### Last session
- Set up mentor-mode rules in `CLAUDE.md` and `AI_Guidelines.md`, including a no-AI-attribution rule for commits and PRs.
- Added a Claude section to `.gitignore` that ignores only `.claude/settings.local.json`, so the rest of `.claude/` can be shared across laptops.
- Created `.gitattributes` with `* text=auto` to normalize line endings across Windows and Mac.
- Reviewed the commands for merging `main` into `dev` and `master`.

### What I learned
- Syncing the raw `~/.claude` folder between laptops is fragile. Git plus a progress journal is the sync layer.
- `core.autocrlf` is per machine; `.gitattributes` travels with the repo.
- `git checkout <receiver>` then `git merge <source>` merges one branch into another.

### Next step
- Commit the `.gitignore`, `.gitattributes` and docs changes, then check `git log -1` for any AI attribution line.
- Decide whether `main` or `master` is the primary branch.
- Start the first small Python module, in mentor mode (see `plan.md`).

### Open questions
- What does git do with a file it decides is binary under `text=auto`?
- Which of `main` and `master` should be primary, and do I need `dev`?
