import tempfile
import unittest
from datetime import date
from pathlib import Path

from hand_script import cli, log

D = date


def e(day, script="greek", minutes=10, **kw):
    return log.make_entry(day, script, minutes, **kw)


class LogTests(unittest.TestCase):
    def test_streaks(self):
        ents = [e(D(2026, 11, d)) for d in (10, 11, 12, 14, 15)]
        self.assertEqual(log.streaks(ents, D(2026, 11, 15)), (2, 3))
        # today not logged yet: streak still counts from yesterday
        self.assertEqual(log.streaks(ents, D(2026, 11, 16)), (2, 3))
        # gap of a full day breaks current streak
        self.assertEqual(log.streaks(ents, D(2026, 11, 17)), (0, 3))
        self.assertEqual(log.streaks([], D(2026, 11, 17)), (0, 0))

    def test_summary(self):
        ents = [
            e(D(2026, 11, 15), minutes=6, characters=24),
            e(D(2026, 11, 15), minutes=5, lines=3),
            e(D(2026, 11, 14), "Hebrew", 20, characters=27),
        ]
        s = log.summarize(ents, D(2026, 11, 15))
        self.assertEqual((s["sittings"], s["days"], s["minutes"]), (3, 2, 31))
        self.assertEqual(s["today_minutes"], 11)
        self.assertTrue(s["daily_minimum_met"])
        self.assertEqual(s["scripts"]["hebrew"]["characters"], 27)
        self.assertEqual(s["scripts"]["greek"]["days"], 1)
        self.assertIn("streak: current 2", log.format_summary(s))

    def test_validation(self):
        with self.assertRaises(ValueError):
            log.make_entry(D(2026, 11, 15), "greek", 0)
        with self.assertRaises(ValueError):
            log.make_entry(D(2026, 11, 15), "greek", -1)
        with self.assertRaises(ValueError):
            log.make_entry(D(2026, 11, 15), " ", 5)

    def test_cli_roundtrip_and_bad_file(self):
        with tempfile.TemporaryDirectory() as d:
            f = str(Path(d) / "sub" / "log.jsonl")
            self.assertEqual(
                cli.main(
                    [
                        "log",
                        "--file",
                        f,
                        "add",
                        "Greek",
                        "--minutes",
                        "12",
                        "--characters",
                        "30",
                        "--date",
                        "2026-11-15",
                        "--focus",
                        "αβγ",
                    ]
                ),
                0,
            )
            self.assertEqual(len(log.read(Path(f))), 1)
            self.assertEqual(cli.main(["log", "--file", f, "summary"]), 0)
            self.assertEqual(cli.main(["log", "--file", f, "add", "greek"]), 2)
            Path(f).write_text("{bad\n", encoding="utf-8")
            self.assertEqual(cli.main(["log", "--file", f, "summary"]), 2)

    def test_read_rejects_malformed_entries(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "l.jsonl"
            for bad in (
                "[1]",
                '{"date":"2026-11-01"}',
                '{"date":"bad","script":"g","minutes":1,"characters":0,"lines":0}',
                '{"date":"2026-11-01","script":"g","minutes":-1,"characters":0,"lines":0}',
            ):
                f.write_text(bad + "\n", encoding="utf-8")
                with self.assertRaises(ValueError) as cm:
                    log.read(f)
                self.assertIn(":1:", str(cm.exception))
                self.assertEqual(cli.main(["log", "--file", str(f), "summary"]), 2)


if __name__ == "__main__":
    unittest.main()
