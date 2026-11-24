---
name: next-ticket
description: Owner-started driver that takes one ready leaf ticket of epic #1 up to a ready pull request (draft first, ready only on green CI). Starting it is the owner's go signal.
argument-hint: "[issue number]"
disable-model-invocation: true
---

# Next ticket

Run once per start. The owner starting this skill is the go signal; nothing here runs on a schedule and nothing starts a second run. One ticket per run. It never merges.

`CLAUDE.md` holds the rules, [`implement-ticket`](../implement-ticket/SKILL.md) holds the steps. Where they differ, `CLAUDE.md` wins.

## Steps

1. **Refresh the queue.** `gh issue view 1` for the epic and its list of child tickets, then `gh issue list --state open --limit 100 --json number,title,labels` and keep only the issues that list names. A `status:blocked` ticket whose blockers are all closed becomes `status:ready` (`gh issue edit <n> --add-label status:ready --remove-label status:blocked`). Also check parents: for each ticket labelled `tracking` or with sub-issues (`gh api repos/jortega0033/thumbnail-and-reel-cover-studio/issues/<n>/sub_issues`), if all its sub-issues are closed, close it with a comment. A ticket with no sub-issues is never closed by this step.
2. **Pick the ticket.** Only leaf tickets are work: a ticket labelled `tracking`, or with open sub-issues, is a container and is never picked. If an issue number was given and it is a container (labelled `tracking` or with open sub-issues), refuse it and list its open sub-issues; otherwise use it after checking it is `status:ready`. Without a number, take the first `status:ready` leaf ticket that is not `status:in-progress` and does not carry `needs-decision`. The order is the epic's table (#9, #10, #11, #2, #3, #4, #13, #5, #6, #7), and inside a parent its sub-issues in the order the API lists them. If none qualifies, say why and stop.
3. **Claim it.** `gh issue edit <n> --add-label status:in-progress --remove-label status:ready`.
4. **Worktree and branch.** From the repository root: `git fetch origin`, then `git worktree add ../thumbnail-and-reel-cover-studio-<n> -b feature/<n>-<short-name> origin/main`. Work only inside that worktree; never on `main`.
5. **Implement.** Run the `implement-ticket` playbook for the ticket: the roles at their steps, `ui-ux-pro-max` at the start of a UI ticket, the `docs/ui-quality.md` check at the end, `unslop` before the pull request, the `CHANGELOG.md` line, the evidence `CLAUDE.md` asks for.
6. **Reviewer files, then draft pull request.** Code Reviewer and Reality Checker have no shell. Before calling them, write the diff and the local evidence to `.claude/state/review/` in the ticket worktree (`git diff --stat origin/main...HEAD`, `git diff origin/main...HEAD`, the check outputs) and name those files in the request. Only after the local checks pass and both have run, `git push` and open a draft pull request from the pull request template with `Closes #<n>` and the epic. If `<n>` is the last open sub-issue of a parent, the description also says `Closes #<parent>`. The review gate hook blocks `gh pr create` and `gh pr ready` until Code Reviewer and Reality Checker have run after the last code edit.
7. **Wait for CI, then ready.** Do not loop, sleep or watch. Bind the pull request to the session if the app offers it, and end the turn with the line "Draft pull request #N is waiting for CI". When the session is woken (a CI event, or the owner says "continue"), read `gh pr checks <N>` once: green on the last commit, then `gh pr ready` and a comment on the issue with the pull request link, the CI run link, the evidence summary and anything left open (including "Owner checks", see the playbook); red, then fix, re-run the local checks and both gates, push and end the turn again; still running, end the turn again with the same line.
8. **Stop.** Do not merge, do not tag, do not pick another ticket. Stop every server or browser you started and report the worktree path.

If a decision named in the ticket blocks the work, label the issue `needs-decision`, comment what is needed, and stop.
