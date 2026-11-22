# Agency Agents roles used in this repository

The Markdown files in `.claude/agents/` whose names start with `engineering-` or `testing-` are copies of role definitions from Agency Agents. They are project-local Claude Code subagents. The file `loop-verifier.md` in the same folder is not from Agency Agents; it belongs to the Loop Engineering setup described in [`LOOP.md`](../../LOOP.md).

## Source and licence

- Upstream: https://github.com/msitarzewski/agency-agents
- Pinned revision: `8ae6164602c95ca78828b148b9052460ee426885` (upstream `main`, 2026-11-09)
- Licence: MIT, "Copyright (c) 2025 AgentLand Contributors". The upstream licence text at the pinned revision is kept unchanged in [`LICENSE`](LICENSE) next to this file. It covers only the copied role files, not the rest of this repository.
- Fetched with `gh api "repos/msitarzewski/agency-agents/contents/<path>?ref=<revision>"`.

## Installed roles

"Upstream SHA-256" is the hash of the file as fetched at the pinned revision. Reviewer roles have one added frontmatter line, `tools: Read, Grep, Glob`, so they cannot edit files or run commands. Nothing else in any file was changed.

| File in `.claude/agents/` | `name:` | Upstream path | Upstream SHA-256 | Local change |
|---|---|---|---|---|
| `engineering-software-architect.md` | Software Architect | `engineering/engineering-software-architect.md` | `b85121691776147bacde26673e68fbbacd6a7f0816d1ca8e203c264d25ce1d30` | added `tools: Read, Grep, Glob` |
| `engineering-code-reviewer.md` | Code Reviewer | `engineering/engineering-code-reviewer.md` | `7509fcc3ea1dda46511b2801996305bf3d4a125576f9655ff0b63df25602f446` | added `tools: Read, Grep, Glob` |
| `engineering-codebase-onboarding-engineer.md` | Codebase Onboarding Engineer | `engineering/engineering-codebase-onboarding-engineer.md` | `07aa548b45887c3ad768efad5fdbf6e57bea639df4f1b74c7e383142f454e2a1` | added `tools: Read, Grep, Glob` |
| `testing-accessibility-auditor.md` | Accessibility Auditor | `testing/testing-accessibility-auditor.md` | `362935907af23839775b9c6162f38c0c5a740542ab4350cb5c5b5a0d9f9a4268` | added `tools: Read, Grep, Glob` |
| `testing-reality-checker.md` | Reality Checker | `testing/testing-reality-checker.md` | `6d32fcdb114233e13902ec6372d50293b120e85d490b5e81d372c29808f988a1` | added `tools: Read, Grep, Glob` |
| `engineering-backend-architect.md` | Backend Architect | `engineering/engineering-backend-architect.md` | `ac717bde4848d7663fff8a3c7edc711fd119256de6a7ce38c036619372f42c99` | none |
| `engineering-frontend-developer.md` | Frontend Developer | `engineering/engineering-frontend-developer.md` | `1ae4cc10b2e0163bd3ed921ad54080b865cd02e591becd8919b64b73fab06dad` | none |
| `testing-test-automation-engineer.md` | Test Automation Engineer | `testing/testing-test-automation-engineer.md` | `4299d038e88387546d645ccbe767b1dfdb7de10da55eba1ab103149972cd2b9b` | none |

## Why these roles

| Role | Use in this repository |
|---|---|
| Software Architect (read-only) | Review a ticket's design against the layering in [`docs/architecture.md`](../../docs/architecture.md) before code is written: the migration path, the split of the browser client into modules, where rendering lives. |
| Code Reviewer (read-only) | Review a diff for correctness, missed edge cases and broken invariants (version check, rounding rule, path handling in export). |
| Codebase Onboarding Engineer (read-only) | Trace a code path and report facts with file and function citations. |
| Accessibility Auditor (read-only) | Review keyboard operation, focus handling, accessible names and status announcements, which the PRD treats as requirements (section 1.5, CHK-F04, CHK-F05). |
| Reality Checker (read-only) | Check claimed evidence against what was actually run before a ticket or the release gate is called done. |
| Backend Architect | Implement work in `cover_studio/*.py` (HTTP layer, storage, validation, rendering). |
| Frontend Developer | Implement work in `cover_studio/static/`. |
| Test Automation Engineer | Build the scripted browser run and the pixel checks. |

The three implementing roles are written for larger stacks (frameworks, cloud services, Playwright or Cypress). In this repository the rules in [`CLAUDE.md`](../../CLAUDE.md) win: Python standard library only, native HTML, CSS and JavaScript, no pip or npm dependencies, no external requests.

## Name collision with user-level agents

A developer who has installed Agency Agents in `~/.claude/agents/` already has agents with the same `name:` values; on the machine used for preparation all eight names existed there. Claude Code gives the project-level definition precedence, so inside this repository the copies here are used, including the read-only tool limits. The upstream names were kept on purpose so that the roles stay recognisable and can be compared with upstream.

A Claude Code session that was already running when these files were added keeps the definitions it loaded at start. Start a new session to pick up the project copies.

## Check that the roles load

From the repository root, in a new session:

```text
claude -p "List the project-level subagents defined in .claude/agents with the tools each one may use. Then run the Reality Checker subagent and ask it which tools it has."
```

The reviewer roles must report exactly `Read, Grep, Glob`.

### What was observed, and what was not

Observed on 2026-11-22 with Claude Code 2.1.323, headless (`claude -p --model haiku`, no MCP servers), from the repository root:

- Software Architect, Code Reviewer, Codebase Onboarding Engineer, Accessibility Auditor, Reality Checker and `loop-verifier` were listed with `Read, Grep, Glob`, and a launched Reality Checker reported exactly those three tools. The user-level copies of these roles have no `tools:` line, so this shows that the project copies were the ones loaded.
- Backend Architect, Frontend Developer and Test Automation Engineer were listed with all tools.
- **Not shown:** that those three are loaded from the project copies. Their files are unchanged from upstream and have no `tools:` line, exactly like a user-level install, and the listing shows names and tools only, not where a definition comes from. Project precedence for these three is assumed from how Claude Code resolves names, not observed. On a machine without a user-level install, check that the three names are listed at all.

## Updating

Fetch the same paths at a newer revision, re-apply the `tools:` line to the five reviewer roles, and update the revision and hashes in this file in the same commit.

## Local change: automatic delegation (2026-11-22)

Two local changes were made to every Agency Agents role in `.claude/agents/` (not to `loop-verifier`):

1. One sentence beginning "Use proactively" was appended to the `description:` line. Claude Code uses that field to decide when to delegate, so the roles now run during ticket work without being named.
2. A section headed `## In this repository` was inserted directly after the closing `---` of the frontmatter, before the upstream text. It is project-specific text written for this repository, not upstream text; the upstream hashes in the table above do not cover it. It names the files the role owns or reviews, the commands from [`CLAUDE.md`](../../CLAUDE.md), the invariants to check, what the role hands back and which parts of the generic text do not apply here. It ends with the sentence "This section and CLAUDE.md override the generic text below wherever they differ."

Nothing else in the role files changed; the upstream text below the inserted section is unmodified.

This supersedes any statement above that a role file is unmodified or that the `tools:` line is the only local change. To compare a role with the pinned upstream file, first remove the whole "In this repository" section (from its heading up to, but not including, the first upstream `#` heading), the "Use proactively" sentence, and the `tools:` line where one was added. When updating from upstream, re-apply all three, and re-read each "In this repository" section against the repository as it is then.

The steps at which each role runs are in `.claude/skills/implement-ticket/SKILL.md`.

Verification, 2026-11-22, Claude Code 2.1.323, from the repository root with the role sections in the working tree: `claude -p "List every project subagent defined in .claude/agents with its exact name and tools, say for each whether its instructions begin with a section titled In this repository, and say whether a skill named implement-ticket is available. Plain list, no commentary." --model haiku` exited 0. It listed Backend Architect, Frontend Developer and Test Automation Engineer with no `tools` field (all tools); Code Reviewer, Codebase Onboarding Engineer, Software Architect, Accessibility Auditor and Reality Checker with `Read, Grep, Glob`; each of the eight as beginning with "In this repository"; `loop-verifier` with `Read, Grep, Glob` and without that section; and the `implement-ticket` skill as available. The answer is a model's reading of the files, so it shows that the files parse and are found, not that a delegated role follows its section; no role was launched in this check.
