import unittest

from src.script_utils import extract_final_script


class TestExtractFinalScript(unittest.TestCase):
    def test_extracts_between_headers(self):
        md = (
            "## 📝 Script Outline\nOutline text here\n\n"
            "## 🎬 Final Script\nLine 1\nLine 2\n\n"
            "## 🏷️ Captions & Hashtags by Platform\nHash stuff\n"
        )
        out = extract_final_script(md)
        self.assertEqual(out.strip(), "Line 1\nLine 2")

    def test_fallback_when_missing_header(self):
        md = "Some random content without expected header"
        out = extract_final_script(md)
        self.assertEqual(out, md)


if __name__ == "__main__":
    unittest.main()
