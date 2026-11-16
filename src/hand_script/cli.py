from __future__ import annotations

import argparse
from pathlib import Path

from . import scripts, sheets


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


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="hand-script")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sheets", help="write printable practice sheets (HTML)")
    s.add_argument("script", help="script id or 'all'")
    s.add_argument("--out", default="sheets")
    s.set_defaults(fn=cmd_sheets)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except KeyError as e:
        print(f"error: {e.args[0]}")
        return 2
