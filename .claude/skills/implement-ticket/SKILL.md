---
name: implement-ticket
description: Playbook for implementing a GitHub issue in this repository from start to pull request, with the project subagents run at fixed steps. Use whenever asked to implement, start, continue or finish a ticket, an issue or an epic child, for example "implement #12" or "work on the next ticket".
argument-hint: "[issue number]"
---

# Implement a ticket

Use this playbook for every implementation ticket in this repository. `CLAUDE.md` holds the commands, the architecture boundaries, the Git workflow and the evidence rules; where this playbook and `CLAUDE.md` differ, `CLAUDE.md` wins.

The project subagents in `.claude/agents/` are part of the work. Delegate to them at the steps below without waiting to be asked. If a step names a role that is not installed, do that step yourself and say so in the pull request.

## Steps

1. **Read the ticket.** `gh issue view <number>` and the epic it belongs to. Check that every prerequisite issue is closed and that no owner decision named in the ticket is still open. If the ticket is blocked, stop and say what blocks it. A ticket labelled `tracking` or with open sub-issues is a container, not work: stop, list its open sub-issues, and leave the choice to the owner (`/next-ticket <sub-issue>`).
2. **Read the rules.** `CLAUDE.md`, then the architecture notes it links to.
3. **Orient and check the approach.** For a UI ticket, first run the `ui-ux-pro-max` skill (design-system search for the product type, `python .claude/skills/ui-ux-pro-max/scripts/search.py "<product type>" --design-system`) and keep to its result and to `docs/ui-quality.md`. Delegate as the table "Before coding" says. Settle open design questions before writing code.
4. **Branch** as the Git workflow in `CLAUDE.md` says. Never work on the default branch.
5. **Implement** inside the ticket's stated scope. Delegate the work to the implementing role that matches the files being changed (table "While coding"). Do not widen scope; note anything else you find as a follow-up.
6. **Test.** Add or change tests for every acceptance criterion and material edge case, then run the checks listed in `CLAUDE.md`. Record each command and its result.
7. **Specialist review.** Run every role in the table "After coding" whose trigger matches the change.
8. **UI quality check.** If the change touches a screen or user-facing copy, check every changed screen against the ten rules in `docs/ui-quality.md` and record the result.
9. **Prose pass.** Run the `unslop` skill over user-facing copy and documentation before the gates, so they judge the final diff; the pull request text gets the same pass when it is written at step 13.
10. **Changelog.** Add one line under Unreleased in `CHANGELOG.md`.
11. **Review gate, always.** Run Code Reviewer on the full diff. Fix every material finding, re-run the checks, and have the reviewer look again until no material finding is left.
12. **Acceptance gate, always.** Run Reality Checker with the ticket's acceptance criteria and the locally recorded evidence. A criterion that needs a person ("by hand in a normal browser", "manual, recorded") is done as far as an agent can (a scripted or headless run, with the evidence) and the rest goes under "Owner checks" in the pull request; Reality Checker accepts that only when the ticket marks the step as manual. It checks that the documented checks ran locally and passed and that CI is configured to run them; it is not asked to confirm a CI result. Do not open the pull request unless it passes.

If a gate finding makes you change code, re-run the checks and, if the change touches a screen or copy, steps 8 to 10, then both gates again, before step 13.
13. **Hand off.** Capture the evidence `CLAUDE.md` asks for. Only with the local checks passing and both gates run after the last code edit, push and open a draft pull request from `.github/pull_request_template.md` that names the issue (`Closes #n`) and the epic; for the last open sub-issue of a parent it also says `Closes #<parent>`. The review gate hook blocks `gh pr create` and `gh pr ready` until Code Reviewer and Reality Checker have run after the last code edit. CI then runs on the draft; do not poll it: end the turn with "Draft pull request #N is waiting for CI" and read `gh pr checks` once when woken. If it fails, fix, re-run the checks and both gates, and push. Mark the pull request ready (`gh pr ready`) only when CI is green on the last commit, and comment on the issue with the CI run link. Only the owner merges; never merge.

## Roles

### Before coding

| Role | Access | Delegate to it |
|---|---|---|
| Codebase Onboarding Engineer | read-only reviewer | At the start of a ticket in an unfamiliar area, to trace the relevant code paths before anything is changed |
| Software Architect | read-only reviewer | Before implementing a ticket that adds or changes a module boundary, data model, storage schema, public API or dependency, to check the approach against the architecture notes |

### While coding

| Role | Access | Delegate to it |
|---|---|---|
| Backend Architect | can edit | When a ticket changes server-side code, HTTP routes, validation, persistence or data migrations |
| Frontend Developer | can edit | When a ticket changes browser-side code such as pages, components, client state, styling or keyboard interaction |
| Test Automation Engineer | can edit | When a ticket adds or changes tests, fixtures or a browser test harness, or when acceptance criteria need new automated checks |

### After coding

| Role | Access | Delegate to it |
|---|---|---|
| Accessibility Auditor | read-only reviewer | After a ticket changes user-facing UI, keyboard handling, focus order or markup |

### Gates that run on every ticket

| Role | Access | Delegate to it |
|---|---|---|
| Code Reviewer | read-only reviewer | After implementing or changing code for a ticket, before a pull request is opened |
| Reality Checker | read-only reviewer | As the acceptance gate of every ticket, after Code Reviewer and before the draft pull request is opened, to check each acceptance criterion against locally recorded evidence; it does not judge CI |

## Rules

- The session or role that wrote a change does not count as its reviewer.
- Read-only reviewers cannot run commands. Write the diff (`git diff --stat origin/main...HEAD`, `git diff origin/main...HEAD`) and the recorded command output to `.claude/state/review/` in the ticket worktree, and name those files, with the acceptance criteria, in the request.
- Do not change agent configuration (`.claude/agents`, `skills`, `hooks`, `settings.json`, `agency-agents`) in a ticket, including through shell commands; the `ask` rules do not cover shell edits.
- Where a role's general advice (frameworks, dependencies, cloud services) conflicts with `CLAUDE.md`, `CLAUDE.md` wins.
- In the pull request description, add a section "Agent roles run" listing each role that ran, what it was asked and its verdict, and any step you did yourself because a role was missing.
