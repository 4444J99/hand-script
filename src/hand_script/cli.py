from __future__ import annotations

import argparse
import os
from datetime import date
from pathlib import Path

from . import log, scripts, sheets


def cmd_sheets(args: argparse.Namespace) -> int:
    ids = scripts.available() if args.script == "all" else [args.script]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for sid in ids:
        data = scripts.load(sid)
        for kind, fn in (("letters", sheets.letter_sheet), ("copy", sheets.copy_sheet)):
            path = out / f"{sid}-{kind}.html"
            path.write_text(fn(data), encoding="utf-8")
            print(path)
    return 0


def _log_path(args: argparse.Namespace) -> Path:
    return Path(args.file or os.environ.get("HAND_SCRIPT_LOG") or log.DEFAULT_PATH)


def cmd_log_add(args: argparse.Namespace) -> int:
    day = date.fromisoformat(args.date) if args.date else date.today()
    entry = log.make_entry(day, args.script, args.minutes, args.characters,
                           args.lines, args.focus, args.note)
    log.append(_log_path(args), entry)
    print(f"logged {entry['script']} {entry['minutes']} min on {entry['date']}")
    return 0


def cmd_log_summary(args: argparse.Namespace) -> int:
    entries = log.read(_log_path(args))
    print(log.format_summary(log.summarize(entries, date.today())))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="hand-script")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sheets", help="write printable practice sheets (HTML)")
    s.add_argument("script", help="script id or 'all'")
    s.add_argument("--out", default="sheets")
    s.set_defaults(fn=cmd_sheets)
    lg = sub.add_parser("log", help="practice log")
    lg.add_argument("--file", help="log path (default data/practice-log.jsonl or $HAND_SCRIPT_LOG)")
    ls = lg.add_subparsers(dest="log_cmd", required=True)
    a = ls.add_parser("add", help="record a practice sitting")
    a.add_argument("script")
    a.add_argument("--minutes", type=int, default=0)
    a.add_argument("--characters", type=int, default=0)
    a.add_argument("--lines", type=int, default=0)
    a.add_argument("--focus", default="")
    a.add_argument("--note", default="")
    a.add_argument("--date", help="YYYY-MM-DD (default today)")
    a.set_defaults(fn=cmd_log_add)
    sm = ls.add_parser("summary", help="totals, per-script, streaks")
    sm.set_defaults(fn=cmd_log_summary)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except KeyError as e:
        print(f"error: {e.args[0]}")
        return 2
    except ValueError as e:
        print(f"error: {e}")
        return 2
