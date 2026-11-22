# Releasing

Only the owner releases. Agents never create a tag or a release.

## What a release is here

Cover Studio is run from a checkout (`python -m cover_studio`); there is no package, installer or deployment. A release is a Git tag on `main` plus a dated section in `CHANGELOG.md`. Milestone M1 is built; no tag exists yet.

## Steps

1. Check that every pull request intended for the release is merged and that CI is green on the tip of `main` (Linux and Windows, Python 3.12 and 3.13).
2. On a fresh clone of `main`, run `python -m unittest discover -s tests -v` and record the `Ran N tests` line. Once `python -m tests.verify` exists (epic #1, ticket #6), run it too.
3. Follow the README "Quickstart" and "Demo flow" from an empty data directory, including a server restart, and stop every server you start.
4. In `CHANGELOG.md`, rename `Unreleased` to the version and date, and add a new empty `Unreleased` section. Merge that change by pull request.
5. Tag the merge commit: `git tag -a vX.Y.Z -m "vX.Y.Z"` and `git push origin vX.Y.Z`. Create the GitHub release from the tag with the changelog section as its notes.

There is nothing to publish to a package registry. Version numbers follow Semantic Versioning; the project database schema version (`user_version`) is a separate number and is described in `docs/architecture.md`.
