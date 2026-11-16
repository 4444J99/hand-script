"""Load script definitions (alphabet data) from the bundled JSON files."""

from __future__ import annotations

import json
from importlib import resources


def available() -> list[str]:
    root = resources.files("hand_script") / "data"
    return sorted(p.name[:-5] for p in root.iterdir() if p.name.endswith(".json"))


def load(script_id: str) -> dict:
    root = resources.files("hand_script") / "data"
    path = root / f"{script_id}.json"
    if not path.is_file():
        raise KeyError(f"unknown script {script_id!r}; available: {', '.join(available())}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["direction"] not in ("ltr", "rtl"):
        raise ValueError(f"{script_id}: bad direction")
    return data
