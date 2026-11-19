"""Printable weekly practice packet: progress summary + graded daily drills."""

from __future__ import annotations

from datetime import date, timedelta
from html import escape

from . import log, sheets

PER_DAY = 4  # letters per day; day 7 is review
LEVELS = {
    1: "Level 1 - trace: dark model, light ghosts, then copy",
    2: "Level 2 - copy: look at the model, write it in the blank cells",
    3: "Level 3 - recall: read the name and sound, write from memory, then check",
}


def level_for(minutes: int) -> int:
    """Graded by total logged minutes in this script."""
    return 1 if minutes < 60 else 2 if minutes < 180 else 3


def forms(script: dict) -> list[dict]:
    out = []
    for letter in script["letters"]:
        for f in letter["practice"]:
            out.append({"form": f, "name": letter["name"], "sound": letter["sound"]})
    return out


def week_letters(script: dict, week_index: int) -> list[list[dict]]:
    """Six days of PER_DAY forms advancing through the alphabet by week, then a review day."""
    fs = forms(script)
    start = (week_index * 6 * PER_DAY) % len(fs)
    days = [[fs[(start + d * PER_DAY + i) % len(fs)] for i in range(PER_DAY)] for d in range(6)]
    days.append([f for day in days for f in day])  # day 7: review of the week
    return days


def week_index(first_day: date, monday: date) -> int:
    return max(0, (monday - first_day).days // 7)


def monday_of(day: date) -> date:
    return day - timedelta(days=day.weekday())


def _drill_row(item: dict, level: int, rtl: bool) -> str:
    kinds = {
        1: ["model", "ghost", "ghost"] + ["blank"] * 5,
        2: ["model"] + ["blank"] * 7,
        3: ["blank"] * 8,
    }[level]
    cells = "".join(sheets._cell(item["form"], k) for k in kinds)
    meta = f"<b>{escape(item['name'])}</b><br>{escape(item['sound'])}"
    return (
        f'<div class="row"><div class="meta">{meta}</div>'
        f'<div class="cells{" rtl" if rtl else ""}">{cells}</div></div>'
    )


def _answer_key(items: list[dict], rtl: bool) -> str:
    """Level 3 hides the models, so print a small key to check against afterwards."""
    chars = " &nbsp; ".join(escape(i["form"]) for i in items)
    d = ' style="direction:rtl;text-align:right"' if rtl else ""
    return f'<div class="sub"{d}>Check against: <span class="key">{chars}</span></div>'


def packet(script: dict, entries: list[dict], today: date) -> str:
    sid = script["id"]
    mine = [e for e in entries if e["script"] == sid]
    minutes = sum(e["minutes"] for e in mine)
    level = level_for(minutes)
    first = min((date.fromisoformat(e["date"]) for e in mine), default=today)
    monday = monday_of(today)
    wi = week_index(monday_of(first), monday)
    rtl = script["direction"] == "rtl"
    summary = escape(log.format_summary(log.summarize(entries, today)))
    copies = script["copy_lines"]
    parts = [
        f"<h1>{escape(script['name'])} - week of {monday.isoformat()}</h1>"
        f'<div class="sub">{escape(LEVELS[level])} &middot; {minutes} min logged in '
        f"{escape(sid)} &middot; daily minimum {log.DAILY_MINIMUM_MINUTES} min.</div>"
        f'<pre class="sum">{summary}</pre>'
        '<div class="sub">Log each sitting: <code>hand-script log add '
        f'{escape(sid)} --minutes N --characters N --focus "..."</code></div>'
    ]
    for d, items in enumerate(week_letters(script, wi)):
        day = monday + timedelta(days=d)
        title = f"Day {d + 1} - {day.strftime('%a %d %b')}" + (" - review" if d == 6 else "")
        c = copies[d % len(copies)]
        text = escape(c["text"])
        style = ' style="direction:rtl;text-align:right"' if rtl else ""
        parts.append(
            f'<section class="day"><h2>{title}</h2>'
            + "".join(_drill_row(i, level, rtl) for i in items)
            + (_answer_key(items, rtl) if level == 3 else "")
            + f'<div class="copy"><div class="src">Copy line: {escape(c["source"])}</div>'
            f'<div class="line model dark"{style}>{text}</div><div class="line"></div></div>'
            '<div class="sub">&#9744; done &nbsp; minutes ____</div></section>'
        )
    css_extra = (
        "<style>.key{font-size:16pt;color:#555}.sum{font-size:9pt;background:#f4f4f4;padding:2mm}"
        ".day{page-break-before:always}.day h2{font-size:13pt;margin:0 0 2mm}</style>"
    )
    page = sheets._page(
        f"{script['name']} weekly packet", "".join(parts), script["direction"], script["font"]
    )
    return page.replace("</head>", css_extra + "</head>", 1)
