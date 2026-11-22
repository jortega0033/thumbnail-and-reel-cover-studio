# Cover Studio

A small offline editor for static thumbnail and reel cover art. Choose a focal point, watch a real crop preview update, add a text overlay, save the project, and reopen it later, even after a restart. Runs entirely on your machine with the Python standard library, SQLite, and native browser JavaScript. No npm or pip packages.

## Status
Baseline milestone (M1): one working preset (Reel cover 9:16, 450x800) over a generated 1200x800 red/green/blue stripe canvas, an editable text overlay, a focal point that moves the crop, and SQLite save/reopen. Batch PNG export, masks, undo, keyboard layer transforms and more presets are planned. See [docs/PRD.md](docs/PRD.md).

What is implemented, planned or still unverified, and where the PRD and the code differ, is recorded in [docs/architecture.md](docs/architecture.md). Rules for contributors and coding agents are in [CLAUDE.md](CLAUDE.md).

## Requirements
Python 3.12 or newer and a modern browser (Chrome is the verification target). No network access is needed.

## Quickstart
```
python -m cover_studio --data-dir ./data --port 8765
```
Open `http://127.0.0.1:8765/`. The server binds only to `127.0.0.1`. Use `--port 0` for an ephemeral port; the actual address is printed on startup. Stop with Ctrl-C. The database is `<data-dir>/cover_studio.sqlite3`.

## Tests
```
python -m unittest discover -s tests -v
```
Tests start real loopback HTTP servers on ephemeral ports with a disposable database.

## Demo flow (about two minutes)
1. Start the server with an empty data directory (commands above) and open the page.
2. Type the title `Sample Reel` and overlay text `Hello <b>world</b> & friends`. The overlay appears literally, not as markup.
3. The crop readout shows `crop x=375 y=0 w=450 h=800`. The preview shows a thin red band, a wide green band and a thin blue band (25 / 400 / 25 px).
4. Tab to Focal X and press the Left arrow repeatedly or type `0`. The readout changes to `x=0` and the preview becomes mostly red.
5. Press Save. The status region says the project is saved.
6. Stop the server with Ctrl-C, start it again with the same `--data-dir`, and reload the page.
7. Select `Sample Reel` in the project list. The title, text, focal point and crop are as saved.
8. Optional conflict check: open two tabs on the same project, save in one, then save in the other. The second shows a conflict message with **Reload latest**.

## API summary
`GET /api/v1/health`, `GET|POST /api/v1/projects`, `GET|PUT /api/v1/projects/{id}`. Writes require a same-origin `Origin` header, JSON content type, and a body of at most 16 KiB. Updates carry the project `version`; a stale version returns 409.

## Limitations
- Single local user; no authentication beyond loopback binding.
- Only generated artwork; no image import or deletion yet.
- Verified by the checks listed in `docs/PRD.md`; portability beyond the tested environment is not claimed.

## License
See [LICENSE](LICENSE).

## Baseline verification

- The unit suite passed on Windows with Python 3.13 and on Ubuntu 24.04 in WSL2 with Python 3.12 (30 tests on Ubuntu). On Linux, use `python3` in the launch and test commands if `python` is unavailable.
- Windows Chrome 157 ran the workflow with external browser requests blocked. Changed the cover text and focal crop, then saved and reopened the cover with both edits intact after a server restart. The browser reported no uncaught page errors.
- 2026-11-22, preparation pass, Windows 11, Python 3.13.14, commit `a989b33`: the unit suite passed (`Ran 30 tests`, `OK`). Demo flow steps 1 to 7 were run by hand in a Chromium 156 browser: crop readout `x=375` at 50 percent and `x=0` after moving Focal X to 0 with the keyboard, markup-like overlay text shown literally, save, server restart, and the same project reopened. Preview pixels at focal 0.5 were red at x=24, green at x=25 and x=424, blue at x=425. Requests were observed to stay on the loopback origin but were not actively blocked. Not reproduced in that pass: the Windows Chrome 157 run with blocked external requests and the Ubuntu run above. Details: [docs/architecture.md](docs/architecture.md), section 9.
