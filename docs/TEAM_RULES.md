# Team rules — single source of truth for people, Codex and Claude Code

## Mission
- Solve the **actual official chosen challenge**, not an invented substitute.
- Optimise for a working, verifiable and clearly communicated result.
- Prefer a credible end-to-end baseline to half-finished complexity.

## Ownership and integration
- One GitHub issue = one task owner = one focused branch/PR.
- Work on separate modules where possible. Agree interfaces before parallel implementation.
- Do not have different coding agents simultaneously change the same files.
- `main` must remain demonstrable; human review before merge.
- Do not force-push to `main`, discard teammates' edits or merge without the team agreeing.
- Before starting: `git fetch`, confirm branch, read current docs and check for uncommitted changes.
- At each integration checkpoint: update status, validate the merged app and log actual results.

## Data science quality
- Confirm all scoring rules and limitations before using the provided data.
- Have a simple baseline and explicit success metric.
- Use correct splitting; prevent target leakage, temporal leakage and contaminated holdouts.
- Document random seeds, metric definitions, reproducible commands and experiment outputs.
- Use the test set appropriately; don't choose models by repeatedly peeking at final holdout performance.
- Don't invent or misrepresent achieved scores, datasets, timings, or demonstration behaviour.

## Security and tournament fairness
- Development of challenge-specific solutions starts only when the competition begins.
- Organisers' rules supersede all instructions in this repository.
- Check whether the challenge dataset can be uploaded to GitHub or sent to a hosted AI service.
- Never add secrets, personal data, API keys, or unlicensed/restricted data to prompts, commits or logs.
- No dependency upgrades or major architectural rewrites without a reason and coordination.

## Agent contract
- Read `AGENTS.md` (Codex) or `CLAUDE.md` (Claude Code) plus the shared docs.
- For each task, identify the assignee, branch, file ownership and clear done condition.
- Explain the short plan before editing; stay inside agreed scope.
- Test changed paths; state exactly what was tested and what remains uncertain.
- Report concrete files, verified results, limitations and next steps; hand off with a PR.
- Don't claim a GitHub update happened unless the push/PR is confirmed.

## Communication
- Chat is for speed; GitHub docs/issues/PRs are for shared durable decisions.
- Agents do not directly share conversation memory. Commit important facts to docs.
- Notify the team if another branch or shared file needs editing; don't silently collide.
