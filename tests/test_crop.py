"""Unit tests for crop math and input validation (CHK-B03, CHK-B04)."""

import unittest

from cover_studio import crop


class CropTests(unittest.TestCase):
    def test_known_crop_positions(self):
        # CHK-B03: focal_x -> crop x, with clamping at both edges.
        cases = {0.5: 375, 0.25: 75, 0.0: 0, 1.0: 750, 0.1: 0, 0.9: 750}
        for focal, expected in cases.items():
            with self.subTest(focal=focal):
                self.assertEqual(crop.compute_crop(focal)["x"], expected)

    def test_crop_size_and_bounds_invariant(self):
        for i in range(0, 101):
            c = crop.compute_crop(i / 100)
            self.assertEqual((c["y"], c["width"], c["height"]), (0, 450, 800))
            self.assertTrue(0 <= c["x"] <= 750)

    def test_center_bands(self):
        # Stripe fixture: red < 400, green < 800, blue otherwise.
        def band(sx):
            return "R" if sx < 400 else "G" if sx < 800 else "B"

        x0 = crop.compute_crop(0.5)["x"]
        self.assertEqual(x0, 375)
        got = {px: band(x0 + px) for px in (24, 25, 424, 425)}
        self.assertEqual(got, {24: "R", 25: "G", 424: "G", 425: "B"})

    def test_half_rounds_up(self):
        # 0.28125 * 1200 - 225 = 112.5 exactly: floor(v + 0.5) gives 113,
        # banker's rounding would give 112.
        self.assertEqual(crop.compute_crop(0.28125)["x"], 113)


class ValidationTests(unittest.TestCase):
    def v(self, payload, **kw):
        kw.setdefault("require_all", False)
        kw.setdefault("require_version", False)
        return crop.validate_project_input(payload, **kw)

    def fields(self, payload, **kw):
        with self.assertRaises(crop.ValidationError) as ctx:
            self.v(payload, **kw)
        return ctx.exception.fields

    def test_defaults_and_trim(self):
        out = self.v({"title": "  Sample Reel  "})
        self.assertEqual(out["title"], "Sample Reel")
        self.assertEqual(out["overlay_text"], "")
        self.assertEqual((out["focal_x"], out["focal_y"]), (0.5, 0.5))

    def test_limits_accept(self):
        self.v({"title": "t" * 80, "overlay_text": "o" * 120})

    def test_rejections(self):
        bad = [
            ({"title": ""}, "title"),
            ({"title": "   "}, "title"),
            ({"title": "t" * 81}, "title"),
            ({"title": 5}, "title"),
            ({"title": "a\nb"}, "title"),
            ({"title": "\ud800"}, "title"),
            ({"title": "ok", "overlay_text": "o" * 121}, "overlay_text"),
            ({"title": "ok", "overlay_text": "a\nb"}, "overlay_text"),
            ({"title": "ok", "overlay_text": None}, "overlay_text"),
            ({"title": "ok", "focal_x": 1.01}, "focal_x"),
            ({"title": "ok", "focal_y": -0.1}, "focal_y"),
            ({"title": "ok", "focal_x": True}, "focal_x"),
            ({"title": "ok", "focal_x": "0.5"}, "focal_x"),
            ({"title": "ok", "focal_x": float("nan")}, "focal_x"),
            ({"title": "ok", "focal_x": float("inf")}, "focal_x"),
            ({"title": "ok", "preset": "square"}, "preset"),
            ({"title": "ok", "bogus": 1}, "bogus"),
            ({}, "title"),
        ]
        for payload, field in bad:
            with self.subTest(payload=payload):
                self.assertIn(field, self.fields(payload))

    def test_non_object(self):
        self.assertIn("body", self.fields([1, 2]))

    def test_update_requires_everything(self):
        f = self.fields({"title": "x"}, require_all=True, require_version=True)
        for name in ("overlay_text", "preset", "focal_x", "focal_y", "version"):
            self.assertIn(name, f)

    def test_version_rules(self):
        base = {"title": "x", "overlay_text": "", "preset": "reel_9_16",
                "focal_x": 0.5, "focal_y": 0.5}
        for bad in (0, -1, 1.5, True, "1"):
            with self.subTest(version=bad):
                self.assertIn("version", self.fields(
                    dict(base, version=bad), require_all=True, require_version=True))
        out = self.v(dict(base, version=3), require_all=True, require_version=True)
        self.assertEqual(out["version"], 3)


if __name__ == "__main__":
    unittest.main()
