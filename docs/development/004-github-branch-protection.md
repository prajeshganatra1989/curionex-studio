# GitHub Branch Protection (Recommended)

Do **not** configure these settings from application code. Apply them in the GitHub repository UI (or org rulesets) when ready.

Path: **Settings → Branches → Branch protection rules** (or **Rules → Rulesets**) for `main`.

## Sensible minimum for a small project

| Setting | Recommendation |
|---------|----------------|
| Require a pull request before merging | **Yes** |
| Require approvals | **Yes** — 1 reviewer is enough for now |
| Require status checks to pass | **Yes** — require `Lint and test backend` (or the workflow job name GitHub shows) |
| Require conversation resolution | **Yes** |
| Restrict force pushes | **Yes** — block force pushes to `main` |
| Restrict deletions | **Yes** — prevent deleting `main` |
| Require linear history | Optional — nice-to-have, not required yet |
| Require signed commits | Optional — skip until the team wants it |

## Why this minimum

- Stops accidental direct commits to `main`.
- Keeps Ruff + pytest as a merge gate.
- Avoids heavy enterprise process while the team is small.

## Related

- CI overview: [001-ci-cd.md](./001-ci-cd.md)
- Branch naming: [002-git-workflow.md](./002-git-workflow.md)
