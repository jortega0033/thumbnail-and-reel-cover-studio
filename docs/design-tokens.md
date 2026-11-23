# Design tokens

The visual system is the Pipenzo "Flow look": a black page, Flow-style alpha layers, one accent (Pipenzo yellow `#FECE02`) and red only for danger. Dark is the primary design; the light block is the matching light theme. The theme follows the operating system colour scheme (`prefers-color-scheme`); there is no switch in the page.

## Source and resync

- Source: `jortega0033/clip-to-reel-studio`, `extension/sidepanel/tokens.css`, commit `a13378ce73e5b27213c9a200fc960ec93afef054` (2026-11-21).
- Copy: `cover_studio/static/tokens.css`, byte for byte. Do not edit it here.
- Resync: copy the file over the old one. Nothing else.
- Served from the `STATIC_FILES` whitelist in `cover_studio/server.py`; `index.html` links it before `style.css`.

## Token names by role

- Surfaces: `--bg`, `--bg-raised`, `--surface`, `--bg-sunken`.
- Text: `--fg`, `--muted`, `--faint`, `--on-media` (text on images, always white).
- Lines: `--border`, `--hairline`, `--control-border`, `--input-border`.
- Accent: `--primary`, `--primary-press`, `--on-primary`, `--focus`. Yellow is used only for the primary action, the current-step marker and the current selection (see "Accent, selection, focus and themes"); the focus ring (`--focus`) is exempt from this limit. Text never sits on a bare alpha layer.
- Status: `--danger`, `--danger-bg`, `--ok`, `--ok-bg`, `--warn-fg`, `--warn-bg`, `--success`, `--info`. Red is only `--danger`.
- Dark block: `--ink`, `--on-ink`, `--on-ink-muted`, `--ink-border`.
- Layers: `--scrim`, `--glass*`, `--state-hover`, `--state-selected`, `--btn-secondary*`, `--ring-accent`. `--state-selected` is a neutral alpha layer and does not mark the current selection; that is a solid `--primary` fill with `--on-primary` text.
- Shape, type, motion: `--radius-*`, `--space-*`, `--font`, `--mono`, `--shadow-*`, `--dur-*`, `--ease-*`.

## Rules

- New UI uses these tokens; no new colour literals (hex, `rgb()`, `hsl()` or named colours) in CSS or JavaScript.
- JavaScript that draws on a canvas reads a token with `getComputedStyle(document.documentElement).getPropertyValue('--token')` (the `token()` helper in `app.js`).
- Allowed literals: colours that are data (the fixture source image bands) and canvas effects that have no token (the overlay text shadow `rgba(0,0,0,0.85)`). Resetting the canvas shadow after the overlay text uses `shadowBlur = 0` and zero offsets, so no colour literal is involved.
- The UI rules in [`ui-quality.md`](ui-quality.md) still apply on top of the tokens.

## Accent, selection, focus and themes

Where a comment in `tokens.css` says something different, these rules take precedence. That covers the header comment and the inline comments on `--primary` and `--state-selected`: they do not list the current selection as a use of yellow, they describe `--state-selected` as a selected row or segment fill, and they list the turn chip and two dots of the source product, which these rules do not allow. The inline comment on `--focus` in the dark block (a focus ring is not a yellow decoration) agrees with the focus rule below. The copy must stay identical to the source, so the comments are not edited here; this document is the rule.

- Current selection (UI rule 8). Decided by the owner on 2026-11-23: the yellow accent is used for the primary action, the current-step marker and the current selection. How (recommended by the orchestrator, adopted under the owner's delegation of the same day): a selection is drawn as a solid `--primary` fill with `--on-primary` text, not only a yellow border (about 1.5:1 against white on light). It also carries a second sign that is not colour (weight, an icon or text) and keeps its existing aria attribute. Never a tint with a same-hue border, and never a thick one-sided border.
- Focus ring: `--focus` is a focus indicator and is exempt from the accent limit, including where it is yellow in dark. A ticket that says the focus style stays unchanged means the rule on `main` after the token pull request. Recommended by the orchestrator, adopted under the owner's delegation of 2026-11-23.
- Themes: contrast checks and no-colour-alone checks cover both the light block and the dark block of `tokens.css`. Recommended by the orchestrator, adopted under the owner's delegation of 2026-11-23.
- Status of the page: the page does not follow the selection rule yet. The current project in the list (`#project-list button[aria-current="true"]` in `style.css`) is still marked with a neutral border, a neutral fill and bold weight. The page follows in ticket work.
