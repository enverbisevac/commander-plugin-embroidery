import importlib.util
import pathlib
import unittest
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("viewer", ROOT / "embroidery_viewer.py")
viewer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(viewer)


class FakeThread:
    color = 0xCC3366


class FakePattern:
    stitches = [[0, 0, 0], [100, 0, 0], [100, 100, 0], [0, 0, 4]]
    threadlist = [FakeThread()]

    def get_as_stitchblock(self):
        yield self.stitches[:3], self.threadlist[0]


class ViewerTests(unittest.TestCase):
    def test_renders_safe_svg_preview(self):
        result = viewer.render_svg(FakePattern(), "sample<&.pes")
        self.assertTrue(result["ok"])
        self.assertEqual(result["kind"], "html")
        self.assertIn("<svg", result["html"])
        self.assertIn("#cc3366", result["html"])
        self.assertNotIn("sample&lt;&amp;.pes", result["html"])
        self.assertEqual(result["meta"], "10.0 × 10.0 mm · 3 stitches · 1 colors")
        self.assertNotIn("<script", result["html"])

    def test_renders_base64_svg_thumbnail(self):
        result = viewer.render_thumbnail(FakePattern(), 220)
        self.assertTrue(result["ok"])
        self.assertEqual(result["mime"], "image/svg+xml")
        self.assertTrue(result["data_base64"])

    def test_converter_rejects_missing_source(self):
        with self.assertRaises(SystemExit):
            viewer.convert({"src": "/definitely/missing.dst", "dst": tempfile.mktemp(suffix=".pes")})


if __name__ == "__main__":
    unittest.main()
