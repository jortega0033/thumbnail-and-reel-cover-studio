# UI quality rules

Ten rules the owner approved on 2026-11-22. They are binding for every screen and every piece of user-facing copy in this repository.

1. No thick accent border on one side of a card, callout, alert, list item or quote (for example `border-left: 4px solid <accent>`). Use spacing, type weight, an icon or a full hairline border instead.
2. No "soft tinted background with a thin border of the same hue" as the default way to mark a status, tag, callout or card. One neutral surface and one clear signal (text, icon or a solid chip) is enough.
3. No gradient text and no purple-to-blue gradient as a default accent.
4. No blur or glass panels, and no drop shadow plus large radius on every card.
5. No emoji used as icons or bullets, and no sparkle marks.
6. No pill or badge on things that are not states. No all-caps, letter-spaced micro labels as section decoration.
7. No centred hero with a slogan in an application screen. Screens open on the user's task.
8. One accent colour, used for the primary action and the current selection. Status colours only for status.
9. Dense, aligned layouts on a consistent spacing scale. No card grid where a table or a list is the right form.
10. User-facing copy is plain and specific: no filler, no exclamation marks, and the same word for the same thing everywhere.

Rule 8 is read together with the "Accent, selection, focus and themes" section of [`design-tokens.md`](design-tokens.md) and owner decision 14: the accent also marks the current step, and `--focus` is a focus indicator that is exempt from the accent limit.

## How they are applied

- A UI ticket starts with the `ui-ux-pro-max` skill (`python .claude/skills/ui-ux-pro-max/scripts/search.py "<product type>" --design-system`) and ends with a check of the changed screens against this file.
- User-facing copy, documentation and pull request text go through the `unslop` skill before the pull request is opened.
- The tailored sections of Frontend Developer, Accessibility Auditor and Code Reviewer name this file in their checklists.
- Enforcement is by the review gate (Code Reviewer on every ticket), not by a script. Rule 1 can be linted; rule 2 cannot be detected reliably from CSS.
- Existing screens that break a rule are listed in the epic's ticket "Bring the existing screens in line with `docs/ui-quality.md`".

Colours come from the Pipenzo tokens in `cover_studio/static/tokens.css`; see [`design-tokens.md`](design-tokens.md).
