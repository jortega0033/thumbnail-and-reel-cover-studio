## Ticket

Closes #

Epic: #1

## What changed

<!-- What the change does and why, in plain words. -->

## Evidence

<!-- Each command you ran and its result, as CLAUDE.md "Evidence before calling a ticket done" asks: commit, OS, Python version, the `Ran N tests` line, browser evidence, acceptance criteria with their checks. -->

| Command | Result |
|---|---|
| `python -m unittest discover -s tests -v` | |

## Agent roles run

<!-- Role, what it was asked, verdict. Code Reviewer and Reality Checker run on every ticket. -->

| Role | Asked to | Verdict |
|---|---|---|
| Code Reviewer | | |
| Reality Checker | | |

## Risks and rollback

<!-- What could go wrong, and how to undo it. -->

## Checklist

- [ ] Branch is `feature/<issue-number>-<short-name>`, cut from `origin/main`
- [ ] CI is green on the last commit
- [ ] Docs changed in this pull request where behaviour, a boundary or a status changed
- [ ] Changed screens checked against `docs/ui-quality.md`; copy and pull request text passed through `unslop`
- [ ] `CHANGELOG.md` has a line under Unreleased
- [ ] Every server or browser process I started is stopped
