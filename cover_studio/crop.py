"""Crop computation and project input validation."""

import math

SOURCE_WIDTH = 1200
SOURCE_HEIGHT = 800
PRESET_ID = "reel_9_16"
OUT_WIDTH = 450
OUT_HEIGHT = 800
MAX_TITLE = 80
MAX_OVERLAY = 120

_BASE_FIELDS = ("title", "overlay_text", "preset", "focal_x", "focal_y")


class ValidationError(Exception):
    """Raised when input is invalid; `fields` maps field name to message."""

    def __init__(self, fields):
        super().__init__("invalid input")
        self.fields = dict(fields)


def compute_crop(focal_x):
    """Return the crop rectangle for a horizontal focal point in [0, 1]."""
    x = int(math.floor(focal_x * SOURCE_WIDTH - OUT_WIDTH / 2 + 0.5))
    x = max(0, min(SOURCE_WIDTH - OUT_WIDTH, x))
    return {"x": x, "y": 0, "width": OUT_WIDTH, "height": OUT_HEIGHT}


def _has_control(text):
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        return True  # lone surrogates cannot be stored
    return any(ord(c) < 32 or 127 <= ord(c) < 160 for c in text)


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_project_input(payload, *, require_all, require_version):
    """Validate a decoded JSON payload and return a cleaned dict.

    With require_all, every project field must be present; otherwise
    title is required and the rest take defaults. With require_version,
    a positive integer `version` is required (and allowed).
    """
    if not isinstance(payload, dict):
        raise ValidationError({"body": "must be a JSON object"})
    errors = {}
    allowed = set(_BASE_FIELDS)
    if require_version:
        allowed.add("version")
    for key in payload:
        if key not in allowed:
            errors[str(key)[:40]] = "unknown field"

    required = set(_BASE_FIELDS) if require_all else {"title"}
    if require_version:
        required.add("version")
    for key in sorted(required):
        if key not in payload:
            errors[key] = "required"

    out = {}
    if "title" in payload:
        v = payload["title"]
        if not isinstance(v, str):
            errors["title"] = "must be a string"
        else:
            v = v.strip()
            if not 1 <= len(v) <= MAX_TITLE:
                errors["title"] = f"must be 1-{MAX_TITLE} characters"
            elif _has_control(v):
                errors["title"] = "must not contain control characters"
            else:
                out["title"] = v

    if "overlay_text" in payload:
        v = payload["overlay_text"]
        if not isinstance(v, str):
            errors["overlay_text"] = "must be a string"
        elif len(v) > MAX_OVERLAY:
            errors["overlay_text"] = f"must be at most {MAX_OVERLAY} characters"
        elif _has_control(v):
            errors["overlay_text"] = "must not contain control characters or newlines"
        else:
            out["overlay_text"] = v
    elif not require_all:
        out["overlay_text"] = ""

    if "preset" in payload:
        if payload["preset"] != PRESET_ID or not isinstance(payload["preset"], str):
            errors["preset"] = f"must be {PRESET_ID}"
        else:
            out["preset"] = PRESET_ID
    elif not require_all:
        out["preset"] = PRESET_ID

    for name in ("focal_x", "focal_y"):
        if name in payload:
            v = payload[name]
            if not _is_number(v):
                errors[name] = "must be a number"
            else:
                try:
                    f = float(v)
                except OverflowError:
                    f = math.inf
                if not math.isfinite(f) or not 0.0 <= f <= 1.0:
                    errors[name] = "must be between 0 and 1"
                else:
                    out[name] = f
        elif not require_all:
            out[name] = 0.5

    if require_version and "version" in payload:
        v = payload["version"]
        if not isinstance(v, int) or isinstance(v, bool) or not 1 <= v < 2**62:
            errors["version"] = "must be a positive integer"
        else:
            out["version"] = v

    if errors:
        raise ValidationError(errors)
    return out
