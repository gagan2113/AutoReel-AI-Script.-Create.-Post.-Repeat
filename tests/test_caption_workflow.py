import unittest

from src.workflow import _parse_json_list


class TestCaptionHelpers(unittest.TestCase):
    def test_parse_json_list_valid(self):
        text = '["A", "B", "C"]'
        self.assertEqual(_parse_json_list(text), ["A", "B", "C"])

    def test_parse_json_list_with_extra(self):
        text = 'Options:\n["One", "Two"]\nThanks'
        self.assertEqual(_parse_json_list(text), ["One", "Two"])

    def test_parse_json_list_fallback_lines(self):
        text = "- First\n- Second\n- Third"
        self.assertEqual(_parse_json_list(text), ["First", "Second", "Third"])


if __name__ == "__main__":
    unittest.main()
