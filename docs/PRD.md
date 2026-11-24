# Cover Studio: PRD and Technical Specification

> This document specifies phase 1 of the program in [#62](https://github.com/jortega0033/thumbnail-and-reel-cover-studio/issues/62). Hour figures in it are early estimates for that phase; its open tickets add up to 92 to 145 hours (2026-11-24). Work that it defers is planned in the later phases only where the program names it.

Status: baseline milestone M1 implemented locally; milestones M2 to M6 are planned. Items marked **[Default]** are proposed defaults that can be changed. Items marked **[Open]** are unresolved.

This document describes the target. The current state of the code, the checks that were actually observed, and the known differences between this document and the repository are recorded in [architecture.md](architecture.md).

## 1. Product definition

### 1.1 Problem and user
A solo creator publishes short videos and posts. Each needs a cover image in several shapes (a 9:16 reel cover, a 16:9 thumbnail, a 1:1 grid tile). Making each by hand in a general-purpose editor means re-picking the crop, re-typing the title, and re-checking that nothing important falls outside the frame. Cover Studio is a small, offline, local editor for static cover art: pick a focal point once, see exactly what each preset keeps, add a text overlay, save the project, and come back to it later.

### 1.2 One end-to-end outcome
The user opens the app, creates a project, names it, types an overlay line, moves the focal point with the keyboard or pointer, watches the crop preview change, saves, restarts the program, reopens the project from the list, and sees the same crop and text.

### 1.3 Scope boundaries
In scope for the whole product: static artwork, local single-user use, generated or user-provided local images, deterministic output.
Out of scope: animation, video editing or review, accounts, cloud sync, network calls, plugins, AI features.

### 1.4 Workflow states
A project moves through: `new` (unsaved form) -> `saved` (stored at version N) -> `dirty` (edited, unsaved) -> `saving` -> `saved` or `error`. A `conflict` state occurs when the stored version has advanced (for example another tab saved). From `conflict` the user may reload the latest version or keep editing and be asked again.

### 1.5 Accessibility
Every control has a visible label. Focal point, title and overlay text are fully operable by keyboard. Focus is always visible. Save and error feedback is announced through `role="status"` and `role="alert"` regions. The preview has a text alternative stating the crop position. Contrast of text and buttons meets WCAG AA. The layout works down to 800x600 without page-level horizontal scrolling.

### 1.6 Smallest durable milestone
M1 (the baseline): a saved static cover from a generated stripe canvas, one aspect preset, an editable text overlay, a focal point that changes a real crop preview, and SQLite save/reopen across restarts.

## 2. Epic and stories

**EPIC-1: From one saved cover to a verified multi-preset export set.** Extend the baseline so a project produces correct, reproducible PNG covers for several presets, with keyboard layer transforms, non-destructive masks, undo, and offline verification.

| ID | Story | Status | Depends on |
|---|---|---|---|
| ST-B1 | Create, edit and list projects through the API and UI | Done (M1) | none |
| ST-B2 | Focal point drives a real crop preview (one preset) | Done (M1) | ST-B1 |
| ST-B3 | Text overlay edit and safe rendering | Done (M1) | ST-B1 |
| ST-B4 | Durable save, reopen after restart, conflict handling | Done (M1) | ST-B1 |
| ST-01 | Multi-preset focal crop with edge clamping | Planned (M2) | ST-B2 |
| ST-02 | Keyboard layer transforms for the text layer | Planned (M3) | ST-B3 |
| ST-03 | Non-destructive masks with undo and redo | Planned (M4) | ST-02 |
| ST-04 | Batch PNG export with manifest | Planned (M5) | ST-01, ST-02, ST-03 |
| ST-05 | Offline pixel and interaction verification harness | Planned (M6) | ST-04 |
| ST-06 | Release integration gate | Planned (M6) | ST-05 |

## 3. Milestones and dependencies
- **M1 Baseline (done locally):** ST-B1 to ST-B4. Gate: all CHK-B checks pass.
- **M2 Presets:** ST-01. Gate: CHK-F01 to CHK-F03.
- **M3 Layers:** ST-02, depends on M1. Gate: CHK-F04, CHK-F05.
- **M4 Masks and history:** ST-03, depends on M3. Gate: CHK-F06, CHK-F07.
- **M5 Export:** ST-04, depends on M2, M3, M4. Gate: CHK-F08, CHK-F09.
- **M6 Verification and release:** ST-05, ST-06. Gate: CHK-F10 to CHK-F12 and a clean run of all earlier checks.

M2 and M3 are independent and can proceed in either order.

## 4. Technical specification

### 4.1 Stack and offline entry points
Python 3.12+ standard library, SQLite (via `sqlite3`), HTML, CSS and native JavaScript. No npm or pip dependencies. No network access is needed or used; all assets are generated or bundled.

Entry point: `python -m cover_studio --data-dir <directory> --port <port>`. The server binds only to `127.0.0.1`. Port 0 picks an ephemeral port and prints it. Tests: `python -m unittest discover -s tests -v`.

### 4.2 Module layout
- `cover_studio/__main__.py`: argument parsing and startup.
- `cover_studio/server.py`: HTTP routing, header checks, static files, error mapping.
- `cover_studio/store.py`: SQLite access and optimistic versioning.
- `cover_studio/crop.py`: crop math and input validation (pure functions).
- `cover_studio/static/`: `index.html`, `app.js`, `style.css`.

### 4.3 Security and request handling
- `Host` must be `127.0.0.1:<port>` or `localhost:<port>`, otherwise 403 `forbidden_host` (this blocks DNS rebinding).
- `POST` and `PUT` require an `Origin` header equal to `http://` plus an allowed host, otherwise 403 `forbidden_origin`.
- JSON bodies are capped at 16384 bytes (413) and must have `Content-Type: application/json` (415).
- A strict Content-Security-Policy forbids inline script and style, and external loads. User text reaches the DOM only through `textContent` and canvas `fillText`.
- Unknown fields, wrong types, NaN and out-of-range numbers are rejected with 400 and a per-field message.

### 4.4 API (v1)
| Method and path | Purpose | Success |
|---|---|---|
| GET `/api/v1/health` | Liveness | 200 `{"status":"ok","app":"cover_studio","schema_version":1}` |
| GET `/api/v1/projects` | List, newest update first | 200 `{"projects":[...]}` |
| POST `/api/v1/projects` | Create | 201 project |
| GET `/api/v1/projects/{id}` | Read | 200 project |
| PUT `/api/v1/projects/{id}` | Replace with version check | 200 project, version+1 |

Errors use `{"error":{"code","message","details"?}}`. Codes: `bad_request`, `not_found`, `method_not_allowed`, `version_conflict` (409, `details.current` holds the stored project), `payload_too_large`, `unsupported_media_type`, `forbidden_host`, `forbidden_origin`, `internal_error`. The full contract is mirrored by the tests.

### 4.5 Data schema
SQLite file `<data-dir>/cover_studio.sqlite3`, WAL mode, `user_version = 1`.

```
projects(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,          -- 1..80 chars, trimmed
  overlay_text TEXT NOT NULL,   -- 0..120 chars, no control characters
  preset TEXT NOT NULL,         -- baseline: 'reel_9_16'
  focal_x REAL NOT NULL,        -- 0..1
  focal_y REAL NOT NULL,        -- 0..1
  version INTEGER NOT NULL,     -- starts at 1, +1 per save
  created_at TEXT NOT NULL,     -- UTC ISO-8601
  updated_at TEXT NOT NULL
)
```
Future schema additions (planned, not implemented): `layers`, `masks`, `history`, `exports` tables, added with a migration that bumps `user_version`.

### 4.6 Main algorithm: focal crop with clamping
Source canvas S is `Sw x Sh` (baseline 1200x800). A preset has output size `Pw x Ph`. The crop is the largest rectangle of the preset's aspect ratio that fits in S, then placed by the focal point.

Baseline (single preset, no rescale): crop is `450 x 800`, `y = 0`, `x = clamp(floor(focal_x * 1200 - 225 + 0.5), 0, 750)`.

Rounding uses floor(v + 0.5) in both Python and JavaScript, never banker's rounding, so server and preview always agree.

General form (planned, ST-01): `cw = min(Sw, Sh * Pw / Ph)`, `ch = cw * Ph / Pw`, `x = clamp(floor(fx * Sw - cw/2 + 0.5), 0, Sw - cw)`, `y = clamp(floor(fy * Sh - ch/2 + 0.5), 0, Sh - ch)`. When the crop is smaller or larger than the output it is scaled with an integer-only nearest or box filter chosen so the result is reproducible.

### 4.7 Invariants
- I1: `0 <= x <= Sw - cw` and `0 <= y <= Sh - ch` for every focal value in [0,1].
- I2: Crop output depends only on stored fields (no clocks, no randomness).
- I3: Server and browser compute identical crop rectangles for the same focal values.
- I4: `version` increases by exactly 1 per successful save; a stale `version` never overwrites newer data.
- I5: A failed save leaves the stored row unchanged.
- I6: User text is never interpreted as markup.

### 4.8 Deterministic compositing (planned, ST-04)
Pixels are 8-bit sRGB. Layers composite in order with integer source-over: `out = (src * a + dst * (255 - a) + 127) // 255` per channel, `a` in 0..255. Masks are 8-bit alpha maps multiplied the same way. Text uses a bundled bitmap font (no system fonts) so output does not vary by host. PNG is written with `zlib` and `struct` using fixed filter 0 and fixed compression level, so the same project always yields byte-identical files. **[Default]** Bundled font is an original 5x7 pixel font authored for this project.

### 4.9 Errors, retry, cancel, restart, multi-tab
- Save failure (network, 4xx, 5xx): the form keeps its edits, shows an alert, and re-enables Save. Retrying sends the same payload. A PUT is idempotent for a given `version`: once it succeeds, a repeat with the old version returns 409, which the UI treats as "already advanced" and offers Reload.
- 409 conflict: show the stored title and version, offer **Reload latest**; local edits are not silently discarded until the user chooses.
- 413/415/400: shown inline with the server message.
- Restart: all state is in SQLite; the server holds no session. Reopening the list reflects stored data. A crash mid-write cannot leave a partial row (single transaction, WAL).
- Multi-tab: two tabs editing one project produce a 409 for the later saver; creation in one tab appears in the other on next list refresh.
- Cancel: **New project** with unsaved edits asks for confirmation. Closing the tab with unsaved edits triggers the browser prompt.
- Database unreadable: server exits non-zero with a plain message at startup instead of serving partial data.

## 5. Deterministic fixtures
**F-STRIPES** (generated, never stored): 1200x800, columns 0-399 red `#e53935`, 400-799 green `#43a047`, 800-1199 blue `#1e88e5`.

Calculated expectations for the 450x800 crop:

| focal_x | crop x | Output bands (red / green / blue) |
|---|---|---|
| 0.5 | 375 | 25 / 400 / 25 |
| 0.0 | 0 | 400 / 50 / 0 |
| 1.0 | 750 | 0 / 50 / 400 |
| 0.25 | 75 | 325 / 125 / 0 |
| 0.1 | 0 (clamped from -105) | 400 / 50 / 0 |

Planned crops for the additional presets on the same 1200x800 source (ST-01, not yet implemented; rounding is floor(v + 0.5)):

| Preset | Crop size | Focal 0 | Focal 0.5 | Focal 1 |
|---|---|---|---|---|
| Square 1:1 | 800x800 | x=0 | x=200 | x=400 |
| Portrait 4:5 | 640x800 | x=0 | x=280 | x=560 |
| Thumbnail 16:9 | 1200x675 | y=0 | y=63 | y=125 |

The values are the focal_x column for square and portrait and the focal_y column for the 16:9 thumbnail, since the other axis has no room to move.

For focal 0.5, pixels in the output at x = 24 red, x = 25 green, x = 424 green, x = 425 blue.

Sample project fixtures: title "Sample Reel", overlay "Hello <b>world</b> & friends" (markup-like text must render literally), overlay of exactly 120 characters, title of 80 characters, and a title with non-ASCII text.

## 6. Acceptance checks
Status key: **Auto** = automated test in `tests/`; **Demo** = scripted browser demo; **Planned** = not implemented. Results are recorded only when actually observed; none are asserted in this document.

### Baseline (M1)
| ID | Story | Check | Kind |
|---|---|---|---|
| CHK-B01 | ST-B1 | `GET /api/v1/health` returns 200 and the documented body. | Auto |
| CHK-B02 | ST-B1 | Create then list shows the project; ordering is newest update first. | Auto |
| CHK-B03 | ST-B2 | Focal 0.5/0.25/0/1/0.1 produce crop x 375/75/0/750/0. | Auto |
| CHK-B04 | ST-B3 | Invalid title (empty, 81 chars), overlay over 120, wrong types, NaN, out-of-range focal, unknown fields all return 400 with field details. | Auto |
| CHK-B05 | ST-B4 | Data written, server stopped, new server on the same data dir returns identical project. | Auto |
| CHK-B06 | ST-B4 | Stale `version` PUT returns 409 with `details.current`; stored row unchanged. | Auto |
| CHK-B07 | ST-B1 | Wrong Host returns 403; write without or with foreign Origin returns 403; oversized body 413; non-JSON content type 415. | Auto |
| CHK-B08 | ST-B3 | Markup-like text round-trips unchanged through the API; static assets contain no `innerHTML` assignment. | Auto |
| CHK-B09 | ST-B1..B4 | Browser demo: create, edit text, move focal with keyboard, save, restart, reopen (see README demo flow). | Demo |
| CHK-B10 | ST-B2 | In the browser the preview's left band is 25 px red at focal 0.5 (sampled pixels x=24,25,424,425). | Demo |

### Future (IDs reserved)
| ID | Story | Check | Kind |
|---|---|---|---|
| CHK-F01 | ST-01 | Each preset's crop satisfies I1 for focal values on a 0.05 grid including 0 and 1. | Planned |
| CHK-F02 | ST-01 | New presets clamp to the documented crop rectangles at focal 0, 0.5 and 1 (second table in section 5). | Planned |
| CHK-F03 | ST-01 | Preset switch keeps the focal point and updates crop readout and overview rectangle. | Planned |
| CHK-F04 | ST-02 | Arrow keys nudge a selected text layer 1 px, Shift+arrow 10 px; position persists. | Planned |
| CHK-F05 | ST-02 | Layer stays within canvas bounds; a visible keyboard alternative exists for each pointer action. | Planned |
| CHK-F06 | ST-03 | A mask hides pixels without altering stored source; removing it restores the original pixels. | Planned |
| CHK-F07 | ST-03 | Undo/redo restores exact prior state across 20 operations and survives reload of saved state. | Planned |
| CHK-F08 | ST-04 | Export of all presets yields PNGs of correct dimensions and a manifest listing name, size, SHA-256. | Planned |
| CHK-F09 | ST-04 | Exporting twice gives byte-identical files and identical manifest hashes. | Planned |
| CHK-F10 | ST-05 | An offline script decodes exported PNGs and checks fixture pixels at x=24,25,424,425. | Planned |
| CHK-F11 | ST-05 | A scripted Chrome run drives the keyboard flow with external requests blocked. | Planned |
| CHK-F12 | ST-06 | Full test suite, quickstart from empty state, and restart check all pass on a fresh checkout. | Planned |

## 7. Baseline versus remaining work
**Built in M1:** API (health, projects list/create/read/update), SQLite store with optimistic versioning, host/origin/size checks, one preset (reel 9:16, 450x800), generated stripe canvas, focal controls (sliders, number inputs, marker keys), live crop preview and overview, text overlay, project list, save/error/conflict states, unit and loopback HTTP tests.

**Still ahead:** more presets and generalized crop (ST-01), keyboard-driven layer transforms (ST-02), masks and undo/redo (ST-03), batch PNG export with manifest (ST-04), offline pixel and browser verification (ST-05), release gate (ST-06). Also not built: importing user images, deleting projects.

## 8. Assumptions
- A1 [Default]: Single user, one machine; no authentication beyond loopback binding.
- A2 [Default]: The baseline preview is drawn on a canvas; the stored project holds only parameters, not pixels.
- A3 [Default]: Further presets: thumbnail 16:9 (1280x720), square 1:1 (1080x1080), portrait 4:5 (1080x1350).
- A4 [Default]: Text overlay is bottom-center in the baseline; free positioning arrives with ST-02.
- A5 [Open]: Whether user-supplied images (rather than generated sources) are in scope for the first public release.
- A6 [Open]: Project deletion semantics (hard delete or archive).
- A7: Browser verification targets desktop Chrome on Linux; portability beyond what is tested is not claimed.
