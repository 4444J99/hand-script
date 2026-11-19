"""Append-only JSONL practice log, summaries and streaks."""

from __future__ import annotations

import itertools
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

DEFAULT_PATH = Path("data/practice-log.jsonl")
DAILY_MINIMUM_MINUTES = 10  # the owner's daily minimum for script copying


def make_entry(
    day: date,
    script: str,
    minutes: int,
    characters: int = 0,
    lines: int = 0,
    focus: str = "",
    note: str = "",
) -> dict:
    if minutes < 0 or characters < 0 or lines < 0:
        raise ValueError("minutes, characters and lines must be >= 0")
    if minutes == 0 and characters == 0 and lines == 0:
        raise ValueError("an entry needs minutes, characters or lines")
    if not script.strip():
        raise ValueError("script is required")
    return {
        "date": day.isoformat(),
        "script": script.strip().lower(),
        "minutes": minutes,
        "characters": characters,
        "lines": lines,
        "focus": focus,
        "note": note,
    }


def append(path: Path, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if raw.strip():
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{n}: invalid JSON ({e.msg})") from e
            out.append(_validate(obj, path, n))
    return out


def _validate(obj: object, path: Path, n: int) -> dict:
    if not isinstance(obj, dict):
        raise ValueError(f"{path}:{n}: entry must be a JSON object")
    for key in ("date", "script", "minutes", "characters", "lines"):
        if key not in obj:
            raise ValueError(f"{path}:{n}: missing key {key!r}")
    try:
        date.fromisoformat(obj["date"])
    except (TypeError, ValueError) as e:
        raise ValueError(f"{path}:{n}: bad date {obj['date']!r}") from e
    for key in ("minutes", "characters", "lines"):
        if not isinstance(obj[key], int) or isinstance(obj[key], bool) or obj[key] < 0:
            raise ValueError(f"{path}:{n}: {key} must be a non-negative integer")
    if not isinstance(obj["script"], str):
        raise ValueError(f"{path}:{n}: script must be a string")
    return obj


def streaks(entries: list[dict], today: date) -> tuple[int, int]:
    """(current, longest) streak of consecutive practice days.

    Current counts back from today, or from yesterday if today is not logged yet.
    """
    days = sorted({date.fromisoformat(e["date"]) for e in entries})
    if not days:
        return 0, 0
    longest = run = 1
    for a, b in itertools.pairwise(days):
        run = run + 1 if b - a == timedelta(days=1) else 1
        longest = max(longest, run)
    have = set(days)
    cur = today if today in have else today - timedelta(days=1)
    current = 0
    while cur in have:
        current += 1
        cur -= timedelta(days=1)
    return current, longest


def summarize(entries: list[dict], today: date) -> dict:
    per = defaultdict(lambda: {"minutes": 0, "characters": 0, "lines": 0, "days": set()})
    by_day = defaultdict(int)
    for e in entries:
        p = per[e["script"]]
        p["minutes"] += e["minutes"]
        p["characters"] += e["characters"]
        p["lines"] += e["lines"]
        p["days"].add(e["date"])
        by_day[e["date"]] += e["minutes"]
    current, longest = streaks(entries, today)
    return {
        "sittings": len(entries),
        "days": len(by_day),
        "minutes": sum(by_day.values()),
        "characters": sum(p["characters"] for p in per.values()),
        "lines": sum(p["lines"] for p in per.values()),
        "today_minutes": by_day.get(today.isoformat(), 0),
        "daily_minimum_met": by_day.get(today.isoformat(), 0) >= DAILY_MINIMUM_MINUTES,
        "current_streak": current,
        "longest_streak": longest,
        "scripts": {s: {**v, "days": len(v["days"])} for s, v in sorted(per.items())},
    }


def format_summary(s: dict) -> str:
    out = [
        f"sittings {s['sittings']} on {s['days']} days: {s['minutes']} min, "
        f"{s['characters']} characters, {s['lines']} lines",
        f"today: {s['today_minutes']}/{DAILY_MINIMUM_MINUTES} min "
        f"({'met' if s['daily_minimum_met'] else 'not yet'})",
        f"streak: current {s['current_streak']}, longest {s['longest_streak']}",
    ]
    for name, v in s["scripts"].items():
        out.append(
            f"  {name}: {v['minutes']} min, {v['characters']} chars, "
            f"{v['lines']} lines, {v['days']} days"
        )
    return "\n".join(out)
