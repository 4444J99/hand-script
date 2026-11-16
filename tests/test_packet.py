import tempfile
import unittest
from datetime import date
from pathlib import Path

from hand_script import cli, log, packet, scripts


class PacketTests(unittest.TestCase):
    def test_levels_graded_by_minutes(self):
        self.assertEqual([packet.level_for(m) for m in (0, 59, 60, 179, 180)], [1, 1, 2, 2, 3])

    def test_week_has_seven_days_and_review_covers_week(self):
        g = scripts.load("greek")
        days = packet.week_letters(g, 0)
        self.assertEqual(len(days), 7)
        self.assertEqual(len(days[6]), 24)
        self.assertEqual(days[0][0]["name"], "alpha")

    def test_weeks_advance_and_wrap(self):
        g = scripts.load("greek")
        self.assertEqual(packet.week_letters(g, 2)[0][0]["name"], "alpha")  # 48 forms wrap after two weeks
        h = scripts.load("hebrew")
        self.assertNotEqual(packet.week_letters(h, 0)[0][0], packet.week_letters(h, 1)[0][0])

    def test_packet_content_and_level(self):
        g = scripts.load("greek")
        today = date(2026, 11, 18)
        e = [log.make_entry(date(2026, 11, 17), "greek", 200, 10)]
        html = packet.packet(g, e, today)
        self.assertIn("week of 2026-11-16", html)
        self.assertIn("Level 3", html)
        self.assertEqual(html.count('class="day"'), 7)
        self.assertIn("200 min logged", html)
        self.assertIn("Level 1", packet.packet(g, [], today))

    def test_rtl_packet(self):
        html = packet.packet(scripts.load("arabic"), [], date(2026, 11, 16))
        self.assertIn("cells rtl", html)

    def test_cli_writes_all(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(cli.main(["packet", "all", "--out", d, "--file", f"{d}/none.jsonl",
                                       "--date", "2026-11-18"]), 0)
            names = sorted(p.name for p in Path(d).iterdir() if p.suffix == ".html")
            self.assertEqual(len(names), 5)
            self.assertIn("greek-week-2026-11-16.html", names)


if __name__ == "__main__":
    unittest.main()
