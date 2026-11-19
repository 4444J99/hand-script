import tempfile
import unittest
from pathlib import Path

from hand_script import cli, scripts, sheets


class SheetTests(unittest.TestCase):
    def test_greek_has_24_letters_with_both_cases(self):
        g = scripts.load("greek")
        self.assertEqual(len(g["letters"]), 24)
        self.assertTrue(all(letter["upper"] and letter["lower"] for letter in g["letters"]))

    def test_hebrew_has_22_letters_and_5_finals(self):
        h = scripts.load("hebrew")
        self.assertEqual(len(h["letters"]), 22)
        forms = [f for letter in h["letters"] for f in letter["practice"]]
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

    def test_copy_lines_exact(self):
        g = scripts.load("greek")
        texts = [c["text"] for c in g["copy_lines"]]
        self.assertIn("μηνιν αειδε θεα Πηληιαδεω Αχιληος", texts)
        self.assertIn("ἄνδρα μοι ἔννεπε Μοῦσα πολύτροπον ὃς μάλα πολλὰ", texts)
        h = scripts.load("hebrew")
        finals = {f for letter in h["letters"] for f in letter["practice"][1:]}
        self.assertEqual(finals, set("ךםןףץ"))

    def test_new_scripts_complete(self):
        counts = {"hiragana": 46, "devanagari": 44, "arabic": 28}
        for sid, n in counts.items():
            d = scripts.load(sid)
            self.assertEqual(len(d["letters"]), n, sid)
            self.assertTrue(d["copy_lines"], sid)
            chars = [letter["lower"] for letter in d["letters"]]
            self.assertEqual(len(set(chars)), n, f"{sid} duplicates")
        self.assertEqual(scripts.load("arabic")["direction"], "rtl")

    def test_new_script_copy_lines_exact(self):
        def texts(i):
            return [c["text"] for c in scripts.load(i)["copy_lines"]]

        self.assertIn("بسم الله الرحمن الرحيم", texts("arabic"))
        self.assertIn("अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजम्", texts("devanagari"))
        self.assertIn("いろはにほへと ちりぬるを", texts("hiragana"))

    def test_arabic_names_distinct(self):
        names = [letter["name"] for letter in scripts.load("arabic")["letters"]]
        self.assertEqual(len(set(names)), 28)

    def test_unknown_script(self):
        with self.assertRaises(KeyError):
            scripts.load("nope")

    def test_cli_writes_files(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(cli.main(["sheets", "all", "--out", d]), 0)
            names = sorted(p.name for p in Path(d).iterdir())
            self.assertEqual(
                names,
                sorted(
                    f"{i}-{k}.html"
                    for i in ["arabic", "devanagari", "greek", "hebrew", "hiragana"]
                    for k in ("copy", "letters")
                ),
            )


if __name__ == "__main__":
    unittest.main()
