---
name: next-ticket
description: Owner-started driver that takes one ready ticket of epic #1 up to a ready pull request. Starting it is the owner's go signal.
argument-hint: "[issue number]"
disable-model-invocation: true
---

# Next ticket

Run once per start. The owner starting this skill is the go signal; nothing here runs on a schedule and nothing starts a second run. One ticket per run. It never merges.

`CLAUDE.md` holds the rules, [`implement-ticket`](../implement-ticket/SKILL.md) holds the steps. Where they differ, `CLAUDE.md` wins.

## Steps

1. **Refresh the queue.** `gh issue view 1` for the epic and its list of child tickets, then `gh issue list --state open --limit 100 --json number,title,labels` and keep only the issues that list names. A `status:blocked` ticket whose blockers are all closed becomes `status:ready` (`gh issue edit <n> --add-label status:ready --remove-label status:blocked`).
2. **Pick the ticket.** If an issue number was given, use it after checking it is `status:ready`. Otherwise take the first `status:ready` ticket in the epic's dependency order (#9, #10, #11, #2, #3, #4, #5, #6, #7) that is not `status:in-progress` and does not carry `needs-decision`. If none qualifies, say why and stop.
3. **Claim it.** `gh issue edit <n> --add-label status:in-progress --remove-label status:ready`.
4. **Worktree and branch.** From the repository root: `git fetch origin`, then `git worktree add ../thumbnail-and-reel-cover-studio-<n> -b feature/<n>-<short-name> origin/main`. Work only inside that worktree; never on `main`.
5. **Implement.** Run the `implement-ticket` playbook for the ticket: the roles at their steps, `ui-ux-pro-max` at the start of a UI ticket, the `docs/ui-quality.md` check at the end, `unslop` before the pull request, the `CHANGELOG.md` line, the evidence `CLAUDE.md` asks for.
6. **Pull request.** Open a draft pull request from the pull request template with `Closes #<n>` and the epic. The review gate hook blocks `gh pr create` and `gh pr ready` until Code Reviewer and Reality Checker have run after the last code edit.
7. **Mark ready.** When the gates pass and CI is green on the last commit (`gh pr checks`), run `gh pr ready` and comment on the issue with the pull request link, the evidence summary and anything left open.
8. **Stop.** Do not merge, do not tag, do not pick another ticket. Stop every server or browser you started and report the worktree path.

If a decision named in the ticket blocks the work, label the issue `needs-decision`, comment what is needed, and stop.
