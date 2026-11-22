# Architecture and status record

This document describes what the code does today, which rules hold it together, and how it compares with [`PRD.md`](PRD.md). The PRD describes the target; this file describes the state. It was written during the preparation pass of 2026-11-22 against commit `a989b33` and must be updated in the same pull request as any change to a boundary, an invariant or a status.

Status words used here:

- **Implemented**: in the source at the commit above, with the test or observation that shows it.
- **Planned**: described in the PRD or in an issue, not in the source.
- **Needs verification**: claimed somewhere, but not observed during the preparation pass.

Line numbers refer to commit `a989b33`.

## 1. Shape of the system

One Python process, standard library only. It serves a JSON API and three static files on `127.0.0.1` and keeps projects in one SQLite file. The browser client is a single script without a framework or a build step. There is no other process, no network access and no installed dependency.

| Layer | File | Responsibility | Must not |
|---|---|---|---|
| Entry point | `cover_studio/__main__.py` | Parse `--data-dir` and `--port`, create the server, print `Listening on http://127.0.0.1:<port>`, exit 2 with a plain message when the database or the port cannot be opened (lines 24 to 30). | Hold logic. |
| HTTP | `cover_studio/server.py` | Host check, Origin check on writes, routing, JSON body rules, security headers, static whitelist, mapping of exceptions to error responses. | Touch SQLite or contain product rules. |
| Rules | `cover_studio/crop.py` | Crop math (`compute_crop`, line 24) and input validation (`validate_project_input`, line 43). Pure functions. | Do I/O or import the rest of the package. |
| Storage | `cover_studio/store.py` | The only SQL in the project. Schema (lines 11 to 23), one connection per operation (line 75), create, get, list, update with the version check. | Be bypassed. |
| Client | `cover_studio/static/index.html`, `app.js`, `style.css` | Form, focal controls, canvas preview and overview, project list, save, conflict and error states. Talks to the server only through `api()` (`app.js` line 227). | Use `innerHTML`, inline script or style, or any external URL. |

Dependencies point one way: `__main__` → `server` → `crop`, `store`; `store` → `crop` (for the derived crop). The client knows only the HTTP API.

## 2. Traced workflow: edit, save, restart, reopen

Each step names where it happens and whether it was observed during the preparation pass (see section 9 for the runs).

1. **Start.** `python -m cover_studio --data-dir D --port N` calls `main()` (`__main__.py` line 17), which calls `create_server` (`server.py` lines 201 to 209). That creates the data directory, opens `Store(<D>/cover_studio.sqlite3)` and binds `ThreadingHTTPServer(("127.0.0.1", port))`. `Store.__init__` (`store.py` lines 63 to 73) switches to WAL, runs `CREATE TABLE IF NOT EXISTS` and sets `user_version` to 1. Observed: the listening line with an ephemeral port.
2. **Page load.** `GET /` and the two files under `/static/` come from the `STATIC_FILES` whitelist (`server.py` lines 13 to 17, `_route_static` lines 172 to 179). `app.js` draws once, calls `loadList()` (line 291) and then opens the most recently updated project, or starts a new one when the list is empty (lines 380 to 389). Observed in a browser: status "New project, not saved" on an empty database.
3. **Edit.** Typing in the overlay field calls `markDirty()` and `render()` (line 224). The focal controls go through `setFocal` (line 146), which rounds to whole percent. `cropX()` (line 39) computes the crop position; `drawPreview` (lines 97 to 116) copies the crop from the generated stripe canvas and draws the text with `fillText`; `drawOverview` (lines 118 to 128) draws the source with the crop rectangle. Observed: readout `crop x=375 y=0 w=450 h=800` at 50 percent, `x=0` after 50 presses of Arrow Down in the Focal X field, and the preview pixels listed in section 9.
4. **Save.** The form submit calls `save()` (line 318). A new project is sent with `POST /api/v1/projects`, an existing one with `PUT /api/v1/projects/{id}` including `version` (lines 328 to 335). Edits typed while the request is in flight are kept: the response then updates only `id` and `version` (lines 336 to 346). Observed: status "Saved" and the project in the list.
5. **Server.** `_handle` (`server.py` line 123) checks the Host header first, then routes. `_create` and `_update` (lines 181 to 195) check the Origin header, read the body with `_read_json` (lines 94 to 120: JSON content type, a Content-Length, at most 16384 bytes, no `NaN` or `Infinity`), and validate with `crop.validate_project_input`.
6. **Storage.** `Store.update` (`store.py` lines 129 to 156) runs `BEGIN IMMEDIATE`, then `UPDATE ... SET version=version+1 ... WHERE id=? AND version=?`. If no row changed and the project exists it raises `VersionConflict` with the stored project, which `server.py` lines 154 to 157 turn into 409 `version_conflict` with `details.current`. `_to_project` (lines 45 to 57) adds the derived `crop` on every read.
7. **Restart and reopen.** The server keeps no session. A new process on the same data directory serves the stored rows, and the page opens the stored project. Observed twice: over HTTP (same rows and versions after a restart) and in a browser (title, overlay, focal point, crop readout and status "Saved" after a restart).

## 3. Data ownership

- The database owns the project row: `title`, `overlay_text`, `preset`, `focal_x`, `focal_y`, `version`, `created_at`, `updated_at`.
- `crop` is derived from `focal_x` on every read (`store.py` line 53) and is never stored. `focal_y` is stored and moves the marker, but has no effect on the crop yet, because the only preset uses the full source height.
- The source image is generated in the browser on each page load (`app.js` lines 28 to 36). No pixels are stored anywhere and the server renders nothing.
- The client holds the form state, a dirty flag and the last known `version` (`state`, `app.js` lines 22 to 25). It is discarded on reload; the browser asks before unloading a dirty page (line 375).

## 4. Invariants and what holds them

| Invariant (PRD 4.7) | Where it is enforced | Test |
|---|---|---|
| I1: the crop stays inside the source | clamp in `crop.py` line 27 and `app.js` line 39 | `test_crop.py` `test_crop_size_and_bounds_invariant` (Python side only) |
| I2: the crop depends only on stored fields | `compute_crop` is a pure function of `focal_x` | `test_crop.py` `test_known_crop_positions` |
| I3: server and browser compute the same crop | the same expression in both files; nothing automated compares them | **none**. Observed by hand for focal 0.5 and 0 only |
| I4: `version` rises by exactly 1 and a stale version never overwrites | `store.py` lines 136 to 155 | `test_api.py` `test_update_increments_version`, `test_stale_version_conflict`, `test_concurrent_updates_single_winner` (eight threads, one winner) |
| I5: a failed save leaves the row unchanged | one transaction with rollback (`store.py` lines 134 to 149) | `test_stale_version_conflict` reads the row back after the 409; `test_validation_errors` checks nothing was created |
| I6: user text is never markup | `textContent`, `value` and `fillText` only in `app.js`; Content-Security-Policy in `server.py` lines 18 to 20 | `test_markup_text_roundtrips`, `test_no_unsafe_dom_or_inline_code` |

Other rules the tests hold: Host must be `127.0.0.1:<port>` or `localhost:<port>` (`test_bad_host`, `test_localhost_host_allowed`); writes need an exact Origin (`test_write_origin_required`); body cap and media type (`test_body_cap_and_media_type`, `test_bad_content_length`); only whitelisted static paths are served (`test_unlisted_paths_404`); the `data-testid` hooks exist (`test_testid_hooks_present`). The schema repeats the limits as `CHECK` constraints (`store.py` lines 14 to 19).

### Number handling

Rounding is `floor(v + 0.5)`, never banker's rounding (`test_half_rounds_up` pins 0.28125 → 113). The whole expression `focal * size - crop / 2 + 0.5` is evaluated in double precision, and the result is only the same in Python and JavaScript because both evaluate it in the same order. Exact arithmetic can differ from it by one pixel. Measured during preparation for the planned 16:9 preset (crop height 675, so the half is 337.5): `0.57 * 800` is `455.99999999999994` in both Python 3.13 and Node 22, so the formula gives `y = 118` where exact arithmetic gives 119; 0.565 and 0.575 behave the same way. The presets with an even crop size (450, 640, 800) showed no such case on a 0.001 grid. Consequence for new presets: expected values in tests and fixtures come from the reference implementation, and both languages keep the operation order.

## 5. PRD checks against the code

| Check | Status | Evidence |
|---|---|---|
| CHK-B01 health | Implemented | `test_api.py` `test_health`; observed over HTTP |
| CHK-B02 create, list, order | Implemented | `test_create_list_get` |
| CHK-B03 crop positions | Implemented | `test_crop.py` `test_known_crop_positions` |
| CHK-B04 validation errors | Implemented | `test_api.py` `test_validation_errors`, `test_crop.py` `test_rejections` |
| CHK-B05 reopen after restart | Implemented | `test_reopen_after_restart` (two servers on one directory, in one process); also observed with two real processes |
| CHK-B06 stale version | Implemented | `test_stale_version_conflict` |
| CHK-B07 host, origin, size, media type | Implemented | `test_bad_host`, `test_write_origin_required`, `test_body_cap_and_media_type` |
| CHK-B08 markup-like text | Implemented | `test_markup_text_roundtrips`, `test_no_unsafe_dom_or_inline_code` |
| CHK-B09 browser demo | Implemented, **manual only** | The PRD calls it a scripted demo; no script exists. Run by hand once during preparation (section 9) |
| CHK-B10 preview pixels | Implemented, **manual only** | No script exists. Sampled by hand once during preparation (section 9) |
| CHK-F01 to CHK-F12 | Planned | No code |

## 6. PRD stories against the code

| Item | Status | Evidence or gap |
|---|---|---|
| ST-B1 create, edit, list | Implemented | `server.py` lines 134 to 149, `store.py`; suite and HTTP run |
| ST-B2 focal crop preview, one preset | Implemented | `crop.py` line 24, `app.js` lines 39 and 97 to 128; browser run |
| ST-B3 text overlay, safe rendering | Implemented | `crop.py` lines 81 to 92, `app.js` lines 101 to 113 |
| ST-B4 save, reopen, conflict | Implemented | `store.py` line 129, `server.py` line 154, `app.js` lines 353 to 356 |
| PRD 1.5 accessibility | Implemented in part; **needs verification** | Labels, `role="status"`, `role="alert"`, a slider role on the marker and a focus outline rule exist (`index.html`, `style.css`). Contrast, the 800x600 layout and the visible focus ring were not checked. No horizontal page scroll at 1024x768 was observed |
| PRD 4.9 two-tab conflict in the browser | **Needs verification** | The code path exists (`app.js` lines 353 to 356, 368 to 373) and the API half is tested; the browser half was not run |
| PRD 4.9 unreadable database exits non-zero | **Needs verification** | `__main__.py` lines 26 to 28 return 2; no test, not run |
| PRD 4.9 retry after a lost response | Differs from the PRD | See drift item 5 |
| README "Windows Chrome 157 ... external browser requests blocked" | **Needs verification** | Not reproduced. The preparation run used Chromium 156 without request blocking |
| README "Ubuntu 24.04 in WSL2 with Python 3.12 (30 tests)" | **Needs verification** | Not reproduced. The suite has 30 tests and passed on Windows |
| ST-01 more presets | Planned | One preset is fixed in `crop.py` line 7, the `CHECK` in `store.py` line 16, `app.js` lines 4 and 329, and the disabled select in `index.html` lines 32 to 34 |
| ST-02 layer transforms | Planned | The text position is computed in `app.js` line 110 (bottom centre). No layer data |
| ST-03 masks, undo and redo | Planned | No code, no tables |
| ST-04 PNG export, manifest, compositor | Planned | No PNG writer, no font, no export route. Text is drawn only by the browser with a system font |
| ST-05 verification harness, ST-06 release gate | Planned | No browser or pixel script |
| Importing images, deleting projects | Not planned in the epic | PRD assumptions A5 and A6 are open |

## 7. Drift between the PRD and the repository

1. **Scripted demo.** PRD section 6 gives CHK-B09 and CHK-B10 the kind "Demo = scripted browser demo". There is no script; both are manual steps. The future harness (ST-05) therefore also has to automate two baseline checks.
2. **Verification target.** PRD assumption A7 and the epic name desktop Chrome on Linux. The README records Windows Chrome 157 and a Python-only run on Ubuntu in WSL2. No Chrome-on-Linux run is recorded anywhere.
3. **Schema.** PRD 4.5 shows the table without constraints. The real table has `CHECK` constraints, among them `preset = 'reel_9_16'` (`store.py` line 16). SQLite cannot alter a `CHECK`, so the first new preset needs a table rebuild inside a migration.
4. **Migrations.** PRD 4.5 says future tables arrive "with a migration that bumps `user_version`". No migration mechanism exists: `Store.__init__` never reads `user_version` and sets it to 1 on every start (line 71), so a database written by a newer version would be opened and relabelled without complaint. The health response reports `schema_version` as a literal 1 (`server.py` line 133), not the store's value.
5. **Retry.** PRD 4.9 says a repeated PUT with the old version returns 409 "which the UI treats as already advanced". The UI shows the generic conflict message with **Reload latest**; it does not recognise that the stored project equals what it just sent. The user-visible result is close, the described behaviour is not implemented.
6. **Crop wording in PRD 4.6 and section 5.** The table "Planned crops" lists crop rectangles in source pixels (for example 1200x675 for 16:9), while assumption A3 lists output sizes (1280x720). Both are right, but the scaling rule between them is only described as "an integer-only nearest or box filter". The rule has to be fixed before any pixel expectation for the new presets can be written.
7. **Exact arithmetic.** PRD 4.6 presents the crop formula as arithmetic. In double precision it differs from exact arithmetic for the planned 16:9 preset at some focal values (section 4, "Number handling"). The PRD does not say which one is the contract.
8. **Preview and export.** PRD 4.8 plans a deterministic compositor with a bundled bitmap font for export, while the preview draws with a system font, a blurred shadow and browser text measurement (`app.js` lines 101 to 113). Unless the preview uses the same renderer, it will not show what is exported, and "layer stays within canvas bounds" (CHK-F05) would be decided on different text sizes in the two places.
9. **Byte-identical PNG.** PRD 4.8 expects the same project to "always" give byte-identical files from a fixed `zlib` level. That holds for two runs on one installation. Whether different `zlib` builds produce the same compressed bytes was not verified; pixel data, not file bytes, is the safe thing to pin in tests.
10. **`.prep/`.** The owner checkout contains an untracked, Git-ignored `.prep/` folder (`contract.md`, `backlog.json`) from the baseline build. It is not in the repository and is not a source of truth; its ticket keys CS-1 to CS-6 correspond to issues #2 to #7.

## 8. Constraints that shape new work

- **Two crop implementations.** Any change to the crop rule lands in `crop.py` and in the client together, with one shared table of inputs and expected outputs. Today only the Python side is tested.
- **No client seam.** `app.js` is one 390-line closure with module-level state. Nothing in it can be called from a test, and four planned features would all edit the same file. The first ticket that needs browser-side logic should split pure logic into modules that take and return plain data; every new file needs an entry in `STATIC_FILES` and the `script-src 'self'` policy allows same-origin modules only.
- **No browser tooling.** There is no Node, npm or Python package in the project, and the rule is that there will be none. A scripted Chrome run therefore has to speak the DevTools protocol with the standard library, which has no WebSocket client.
- **One trust boundary.** Writes are protected only by the Host and Origin checks. A route that writes files (export) must build paths from fixed names and validated numbers, never from request text, and must stay inside the data directory.
- **Body cap.** 16384 bytes per request. Any larger document (for example a persisted history) has to fit or the cap has to be changed deliberately, with its test.
- **Threading.** `ThreadingHTTPServer` with one SQLite connection per operation. Long work in a request (rendering, export) runs on a request thread; keep reads short and writes in one transaction.
- **Timestamps.** `updated_at` has one-second resolution; list order falls back to `id DESC` inside the same second (`store.py` line 124).

## 9. Verification record

Preparation pass, 2026-11-22, Windows 11, Python 3.13.14, commit `a989b33` (the preparation branch changes no file under `cover_studio/` or `tests/`).

| What | Result |
|---|---|
| `python -m unittest discover -s tests -v` | `Ran 30 tests in 11.807s`, `OK` |
| `python -m cover_studio --data-dir <temporary> --port 0`, driven over HTTP | `Listening on http://127.0.0.1:<port>`; health 200 with the documented body; create 201 with `crop.x = 0` at focal 0; update 200 with version 2 and `crop.x = 375`; stale update 409 `version_conflict`; write without Origin 403 `forbidden_origin`; `GET /` and `/static/app.js` 200. After stopping the process and starting a new one on the same directory, the list returned the same projects and versions |
| README demo flow, steps 1 to 7, in a Chromium 156 browser (not Google Chrome, not Linux) | Readout `crop x=375 y=0 w=450 h=800`; overlay `Hello <b>world</b> & friends` shown as text, no `<b>` element created; 50 presses of Arrow Down in Focal X gave `crop x=0`; Save gave status "Saved"; after a server restart and a page load the title, overlay, focal point, readout and status were as saved. Every request went to the loopback origin; no console error |
| CHK-B10 sample at focal 0.5, preview row 10 | x=24 `229,57,53` (red), x=25 `67,160,71` (green), x=424 green, x=425 `30,136,229` (blue) |

Not done in this pass: external requests were not blocked, only observed to be absent; Google Chrome and Linux were not used; step 8 of the demo (two tabs) was not run; accessibility was not audited.

## 10. Where the remaining work is tracked

Epic [#1](https://github.com/jortega0033/thumbnail-and-reel-cover-studio/issues/1) holds the order of the tickets, the estimates, the finish line and the shared decisions S1 to S11. The table maps the gaps recorded above to the issues that deal with them. It was added on 2026-11-22, when the issues were written. The statuses in sections 5 to 7 change only in the pull requests that implement the work.

| Gap recorded in this document | Issue |
|---|---|
| No migration path, `user_version` set unconditionally, the preset `CHECK` (drift items 3 and 4); no test for the unreadable database (section 6) | #9 |
| CHK-B09 and CHK-B10 are manual, invariant I3 has no test, no client seam, no browser tooling (drift item 1, section 8); the two-tab conflict was never run in a browser (section 6) | #10 |
| Preview and export would use different renderers, the scaling rule is open, byte-identical PNG files (drift items 6, 8 and 9) | #11 |
| ST-01 more presets; which arithmetic is the crop contract (drift item 7) | #2 |
| ST-02 layer transforms | #3 |
| ST-03 masks, undo and redo | #4 |
| ST-04 export and manifest (the compositor, the font and the PNG writer are built in #11) | #5 |
| ST-05 verification harness (the Chrome driver is built in #10, the PNG decoder in #11) | #6 |
| ST-06 release gate; verification target Chrome on Linux (drift item 2); accessibility still unverified (section 6) | #7 |
| Retry wording of PRD 4.9 (drift item 5), importing images, deleting projects | outside the epic |
