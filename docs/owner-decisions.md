# Owner decisions

A dated record of the decisions the owner made for this repository, so the rules do not depend on anyone's memory of a conversation. Changing any entry needs the owner; an agent that finds a decision blocking a ticket stops and says so.

| # | Decision | Date | Implemented in |
|---|---|---|---|
| 1 | The instructions, tooling and playbook live on the default branch (`main`). | 2026-11-22 | `CLAUDE.md`, `.claude/` |
| 2 | Persona agents run automatically during ticket work and carry instructions tailored to this project. | 2026-11-22 | `.claude/agents/`, `.claude/skills/implement-ticket/SKILL.md` |
| 3 | Every open ticket is about app implementation; tooling is installed, not ticketed. | 2026-11-22 | `.github/ISSUE_TEMPLATE/implementation-ticket.md` |
| 4 | Agents may take a ticket up to a ready pull request. Only the owner merges and releases. | 2026-11-22 | `CLAUDE.md` "Delivery workflow", `.claude/skills/next-ticket/SKILL.md`, `docs/RELEASING.md`, `.github/CODEOWNERS` |
| 5 | No scheduler. Ticket work starts only on the owner's go signal (`/next-ticket`), because the repository is used to train AI models. | 2026-11-22 | `.claude/skills/next-ticket/SKILL.md` (`disable-model-invocation: true`), `LOOP.md` |
| 6 | A review gate hook blocks opening or readying a pull request until the gate roles have run after the last code edit. | 2026-11-22 | `.claude/hooks/role_gate.py`, `.claude/settings.json` |
| 7 | Loop Engineering stays at L1, report-only and unscheduled. | 2026-11-22 | `LOOP.md`, `loop-constraints.md` |
| 8 | Continuous integration runs on Linux and Windows; the default branch requires a pull request and green checks. | 2026-11-22 | `.github/workflows/ci.yml` (branch protection is set on GitHub, not in the repository) |
| 9 | Permission rules: documented commands are allowed; force pushes, pushes to the default branch, merges, releases and reads of secrets are denied; edits to CI, agent configuration and Loop files ask first. | 2026-11-22 | `.claude/settings.json` |
| 10 | Open decisions on tickets are settled with the ticket's stated default (list below). | 2026-11-22 | The issues named below |
| 11 | Rust is verified in CI only. Not applicable here: this repository has no Rust. | 2026-11-22 | none |
| 12 | The ten UI rules in `docs/ui-quality.md` are binding, and the `ui-ux-pro-max` and `unslop` skills are installed and used for UI work and for copy. | 2026-11-22 | `docs/ui-quality.md`, `.claude/skills/ui-ux-pro-max/`, `.claude/skills/unslop/`, `.claude/skills/implement-ticket/SKILL.md` |
| 13 | Visual system: Pipenzo Flow look tokens (docs/design-tokens.md). SDLC kit version: jortega0033/sdlc-kit v1.0.0. | 2026-11-23 | `cover_studio/static/tokens.css`, `docs/design-tokens.md` |
| 14 | Selection, focus and themes: the yellow accent covers the primary action, the current-step marker and the current selection (a selection is a solid `--primary` fill with `--on-primary` text, a non-colour sign and the aria attribute); `--focus` is exempt from the accent limit; contrast checks cover light and dark. The owner decided the selection rule on 2026-11-23. The "How", the focus rule and the theme rule were recommended by the orchestrator and adopted under the owner's delegation of the same day. | 2026-11-23 | `docs/design-tokens.md` (section "Accent, selection, focus and themes"); page changes follow in ticket work |

## Entry 10: open decisions settled by the ticket default

Epic #1 lists these under "Open decisions (defaults apply unless the owner changes them)"; #3 and #4 repeat their model defaults.

| Issue | Decision | Default applied |
|---|---|---|
| #1 | Preview and export renderer | One renderer for both (#11), not a browser-drawn preview plus an export-only compositor |
| #1 | How Chrome is driven | From Python with the standard library; Node is not used |
| #3 | Rotation, scale, glyphs | Quarter turns, integer scale 1 to 40, ASCII glyphs with a replacement box for the rest |
| #11, #2 | Automatically placed text | Shrinks until it fits the canvas (S6); top margin equals the side margin |
| #3 | Text placement scope | Per preset |
| #4 | Mask scope | Masks in source pixels on the artwork only; black behind hidden artwork |
| #4 | History scope | Excludes title, overlay text and preset selection |
| #5 | Export storage | Writes a saved version only; no `exports` table |
| #2 | Crop arithmetic | Double precision (S3), including cases that differ from exact arithmetic by one pixel |
| #5 | Byte identity of PNG files | Promised per installation; pinned hashes are of decoded pixels |
| #7 | Gate host | Chrome on Linux (PRD A7). A Windows-only finish needs the owner's acceptance in #7: flag in issue |
| #1 | Outside this batch | Importing images, deleting projects, recognising a repeated save as "already advanced" (PRD 4.9) |
