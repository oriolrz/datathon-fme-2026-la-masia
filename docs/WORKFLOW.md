# Team workflow — GitHub + Claude Code + Codex

## Before the challenge starts (organisational preparation only)
1. Add all four team members as collaborators to this private repository.
2. Confirm each person can clone it, create a branch, push a harmless docs-only change and open a PR.
3. Install and authenticate local tools: Git, VS Code, Python, Claude Code and/or Codex.
4. Do not develop challenge-specific code before the official start.
5. Everyone reads the entry-point AI instructions and the shared project docs.

## During the Datathon
1. Choose one official challenge. Fill in `docs/BRIEF.md` with exact objective, data constraints and scoring.
2. Define a baseline and agree on interfaces and expected file ownership.
3. Create GitHub issues with specific owner, accepted scope, paths, deliverables and tests.
4. Branch from the newest `main`: e.g. `feature/cesc-eda`, `feature/dani-baseline`.
5. Give the coding agent ONE bounded issue at a time.
6. Run relevant tests and record actual outputs.
7. Push the work branch; open a pull request with the PR template.
8. Another teammate reviews, merges, and checks the integration on `main`.
9. Update `docs/STATUS.md`, `docs/DECISIONS.md` and `docs/EXPERIMENTS.md`.
10. At least every 2–3 hours, run an end-to-end integration checkpoint.

## Safe Git commands (example)
```bash
git switch main
git pull --ff-only
git switch -c feature/yourname-task
# Implement only your accepted scope
git status
git add path/to/your/files
git commit -m "feat: describe the task"
git push -u origin feature/yourname-task
# Open a pull request on GitHub; merge only after review
```

Avoid blind `git reset --hard`, force pushes, and shared-branch concurrent edits.

## Agent prompt (copy after the challenge starts)
```text
Read AGENTS.md (Codex) or CLAUDE.md (Claude Code), plus
docs/TEAM_RULES.md, docs/BRIEF.md, docs/STATUS.md,
docs/DECISIONS.md and docs/WORKFLOW.md.

Assigned GitHub issue and owner: [ISSUE / PERSON]
My branch: [BRANCH]
Files/modules I own: [EXACT PATHS]
Input/output contracts: [IF RELEVANT]
Definition of done: [MEASURABLE TESTS / OUTPUTS]

First inspect git status and the shared docs, then propose a minimal plan.
Implement only this scope. Run tests and report commands and real outputs.
Do not overwrite others' work, merge, force-push, invent scores,
upload restricted data or reveal credentials.
Return a handoff summary suitable for the pull request.
```

## Checkpoints
- Short team sync once the challenge and architecture are selected.
- Integration and updated statuses approximately every 2–3 hours.
- Freeze new features with sufficient time to verify the submission and rehearse.
