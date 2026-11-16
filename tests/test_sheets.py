import tempfile
import unittest
from pathlib import Path

from hand_script import cli, scripts, sheets


class SheetTests(unittest.TestCase):
    def test_greek_has_24_letters_with_both_cases(self):
        g = scripts.load("greek")
        self.assertEqual(len(g["letters"]), 24)
        self.assertTrue(all(l["upper"] and l["lower"] for l in g["letters"]))

    def test_hebrew_has_22_letters_and_5_finals(self):
        h = scripts.load("hebrew")
        self.assertEqual(len(h["letters"]), 22)
        forms = [f for l in h["letters"] for f in l["practice"]]
        self.assertEqual(len(forms), 27)

    def test_letter_sheet_rows_and_direction(self):
        h = scripts.load("hebrew")
        html = sheets.letter_sheet(h)
        self.assertEqual(html.count('class="row"'), 27)
        self.assertIn("cells rtl", html)
        self.assertNotIn("cells rtl", sheets.letter_sheet(scripts.load("greek")))

    def test_copy_sheet_contains_text_and_escapes(self):
        g = scripts.load("greek")
        g["copy_lines"] = [{"source": "<x>", "text": "α&β", "gloss": "g"}]
        html = sheets.copy_sheet(g)
        self.assertIn("&lt;x&gt;", html)
        self.assertIn("α&amp;β", html)

    def test_unknown_script(self):
        with self.assertRaises(KeyError):
            scripts.load("nope")

    def test_cli_writes_files(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(cli.main(["sheets", "all", "--out", d]), 0)
            names = sorted(p.name for p in Path(d).iterdir())
            self.assertEqual(names, ["greek-copy.html", "greek-letters.html",
                                     "hebrew-copy.html", "hebrew-letters.html"])


if __name__ == "__main__":
    unittest.main()
