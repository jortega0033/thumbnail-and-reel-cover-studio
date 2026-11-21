"""SQLite persistence for projects."""

import os
import sqlite3
from datetime import datetime, timezone

from .crop import compute_crop

SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 80),
  overlay_text TEXT NOT NULL CHECK(length(overlay_text) <= 120),
  preset TEXT NOT NULL CHECK(preset = 'reel_9_16'),
  focal_x REAL NOT NULL CHECK(focal_x >= 0.0 AND focal_x <= 1.0),
  focal_y REAL NOT NULL CHECK(focal_y >= 0.0 AND focal_y <= 1.0),
  version INTEGER NOT NULL CHECK(version >= 1),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
)
"""

_COLUMNS = ("id, title, overlay_text, preset, focal_x, focal_y, "
            "version, created_at, updated_at")


class NotFound(Exception):
    """The requested project does not exist."""


class VersionConflict(Exception):
    """The supplied version does not match; `current` is the stored project."""

    def __init__(self, current):
        super().__init__("version conflict")
        self.current = current


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _to_project(row):
    return {
        "id": row[0],
        "title": row[1],
        "overlay_text": row[2],
        "preset": row[3],
        "focal_x": row[4],
        "focal_y": row[5],
        "crop": compute_crop(row[4]),
        "version": row[6],
        "created_at": row[7],
        "updated_at": row[8],
    }


class Store:
    """Project store using one SQLite connection per operation."""

    def __init__(self, path):
        self.path = os.fspath(path)
        directory = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(directory, exist_ok=True)
        conn = self._connect()
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(_SCHEMA)
            conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        finally:
            conn.close()

    def _connect(self):
        conn = sqlite3.connect(self.path, timeout=5.0, isolation_level=None)
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def create(self, data):
        """Insert a project from cleaned input and return it."""
        now = _now()
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            try:
                cur = conn.execute(
                    "INSERT INTO projects(title, overlay_text, preset, focal_x, "
                    "focal_y, version, created_at, updated_at) "
                    "VALUES(?,?,?,?,?,1,?,?)",
                    (data["title"], data["overlay_text"], data["preset"],
                     data["focal_x"], data["focal_y"], now, now))
                row = conn.execute(
                    f"SELECT {_COLUMNS} FROM projects WHERE id=?",
                    (cur.lastrowid,)).fetchone()
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
            return _to_project(row)
        finally:
            conn.close()

    def get(self, project_id):
        """Return one project or raise NotFound."""
        conn = self._connect()
        try:
            row = conn.execute(
                f"SELECT {_COLUMNS} FROM projects WHERE id=?",
                (project_id,)).fetchone()
        finally:
            conn.close()
        if row is None:
            raise NotFound(project_id)
        return _to_project(row)

    def list(self):
        """Return all projects, most recently updated first."""
        conn = self._connect()
        try:
            rows = conn.execute(
                f"SELECT {_COLUMNS} FROM projects "
                "ORDER BY updated_at DESC, id DESC").fetchall()
        finally:
            conn.close()
        return [_to_project(r) for r in rows]

    def update(self, project_id, data):
        """Update a project if data['version'] matches the stored version."""
        now = _now()
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            try:
                cur = conn.execute(
                    "UPDATE projects SET title=?, overlay_text=?, preset=?, "
                    "focal_x=?, focal_y=?, version=version+1, updated_at=? "
                    "WHERE id=? AND version=?",
                    (data["title"], data["overlay_text"], data["preset"],
                     data["focal_x"], data["focal_y"], now,
                     project_id, data["version"]))
                row = conn.execute(
                    f"SELECT {_COLUMNS} FROM projects WHERE id=?",
                    (project_id,)).fetchone()
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
        finally:
            conn.close()
        if row is None:
            raise NotFound(project_id)
        if cur.rowcount != 1:
            raise VersionConflict(_to_project(row))
        return _to_project(row)
