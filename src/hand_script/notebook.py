"""Notebook practice protocol (HS-F001) and observable milestone ledger (thread 3377c206)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hand_script.scripts import ScriptCatalog, load_script_catalog

EXPECTED_LOG_SCHEMA = "hand-script.practice-session/1"
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

PROTOCOL_STEPS: tuple[tuple[str, str, float], ...] = (
    (
        "warm_up",
        "Write baseline strokes, curves, or radicals slowly with focus on proportion.",
        0.15,
    ),
    (
        "copying",
        "Copy a short canonical line or glyph sequence attentively onto physical paper.",
        0.25,
    ),
    (
        "memory_rewrite",
        "Cover the exemplar and rewrite the target sequence from visual-motor recall.",
        0.20,
    ),
    (
        "observation",
        "Annotate recurring graphemes, diacritics, positional allographs, or roots.",
        0.15,
    ),
    (
        "composition",
        "Write one original variation, word recombination, or script adaptation.",
        0.15,
    ),
    (
        "reflection",
        "Record one concise note on friction, legibility, or sound-sign mapping.",
        0.10,
    ),
)

VALID_STEP_IDS = frozenset(step_id for step_id, _, _ in PROTOCOL_STEPS)

OBSERVABLE_MILESTONES: dict[str, str] = {
    "inventory_recognition": (
        "Name and distinguish core signs, positional variants, and diacritics on sight."
    ),
    "guided_copying": ("Copy short lines legibly on ruled paper with consistent stroke direction."),
    "memory_recall": (
        "Reproduce practiced words or glyph blocks from recall without exemplar prompts."
    ),
    "mapping_explanation": (
        "State explicitly what each sign maps to (phoneme, consonant root, mora, or morpheme)."
    ),
    "delayed_readback": (
        "Read back one's own handwritten notebook lines accurately after a multi-day delay."
    ),
    "native_review": (
        "Have handwritten pages checked for legibility and proportion by a fluent reader."
    ),
}


class NotebookError(ValueError):
    """Raised when a session plan request or JSONL practice log entry is invalid."""


@dataclass(frozen=True)
class PlannedStep:
    step_id: str
    minutes: int
    instruction: str


@dataclass(frozen=True)
class SessionPlan:
    script_id: str
    script_name: str
    total_minutes: int
    ruling: str
    direction: str
    focus_glyphs: tuple[str, ...]
    passage_ref: str | None
    steps: tuple[PlannedStep, ...]
    scope_note: str


@dataclass(frozen=True)
class PracticeLogEntry:
    schema: str
    date: str
    script_id: str
    minutes: int
    completed_steps: tuple[str, ...]
    milestones_demonstrated: tuple[str, ...]
    passage_ref: str | None
    notes: str


def plan_session(
    script_id: str,
    *,
    minutes: int = 20,
    passage_ref: str | None = None,
    catalog: ScriptCatalog | None = None,
) -> SessionPlan:
    if minutes < 6 or minutes > 120:
        raise NotebookError("session duration must be between 6 and 120 minutes")
    cat = catalog or load_script_catalog()
    spec = cat.get_script(script_id)

    allocated = [max(1, round(minutes * weight)) for _, _, weight in PROTOCOL_STEPS]
    drift = minutes - sum(allocated)
    # Adjust copying step (index 1) first so total matches requested minutes exactly.
    allocated[1] = max(1, allocated[1] + drift)
    if sum(allocated) != minutes:
        allocated[0] = max(1, allocated[0] + (minutes - sum(allocated)))

    steps = tuple(
        PlannedStep(
            step_id=PROTOCOL_STEPS[idx][0],
            minutes=allocated[idx],
            instruction=PROTOCOL_STEPS[idx][1],
        )
        for idx in range(len(PROTOCOL_STEPS))
    )
    return SessionPlan(
        script_id=spec.id,
        script_name=spec.name,
        total_minutes=minutes,
        ruling=spec.ruling,
        direction=spec.direction,
        focus_glyphs=tuple(g.glyph for g in spec.exemplars[:6]),
        passage_ref=passage_ref,
        steps=steps,
        scope_note=(
            "Handwriting protocol builds grapheme encoding and motor recall; "
            "track comprehension, morphology, and delayed readback separately via "
            "observable milestones rather than percent-fluency claims."
        ),
    )


def parse_practice_log_entry(
    raw: dict[str, Any],
    *,
    line_no: int = 1,
    valid_scripts: set[str] | None = None,
) -> PracticeLogEntry:
    ctx = f"line {line_no}"
    if not isinstance(raw, dict):
        raise NotebookError(f"{ctx}: log entry must be a JSON object")
    schema = raw.get("schema")
    if schema != EXPECTED_LOG_SCHEMA:
        raise NotebookError(
            f"{ctx}: unsupported schema '{schema}' (expected '{EXPECTED_LOG_SCHEMA}')"
        )
    date = raw.get("date")
    if not isinstance(date, str) or not _ISO_DATE_RE.match(date):
        raise NotebookError(f"{ctx}: invalid ISO date '{date}' (expected YYYY-MM-DD)")
    script_id = raw.get("script_id")
    if not isinstance(script_id, str) or not script_id.strip():
        raise NotebookError(f"{ctx}: missing script_id")
    if valid_scripts is not None and script_id not in valid_scripts:
        raise NotebookError(f"{ctx}: unknown script_id '{script_id}'")
    minutes = raw.get("minutes")
    if not isinstance(minutes, int) or minutes < 1 or minutes > 300:
        raise NotebookError(f"{ctx}: minutes must be an integer between 1 and 300")

    steps_raw = raw.get("completed_steps")
    if not isinstance(steps_raw, list) or not steps_raw:
        raise NotebookError(f"{ctx}: completed_steps must be a non-empty list")
    completed_steps: list[str] = []
    for st in steps_raw:
        if not isinstance(st, str) or st not in VALID_STEP_IDS:
            raise NotebookError(f"{ctx}: invalid protocol step '{st}'")
        if st not in completed_steps:
            completed_steps.append(st)

    milestones_raw = raw.get("milestones_demonstrated", [])
    if not isinstance(milestones_raw, list):
        raise NotebookError(f"{ctx}: milestones_demonstrated must be a list")
    milestones: list[str] = []
    for ms in milestones_raw:
        if not isinstance(ms, str) or ms not in OBSERVABLE_MILESTONES:
            raise NotebookError(f"{ctx}: unknown milestone '{ms}'")
        if ms not in milestones:
            milestones.append(ms)

    passage_ref = raw.get("passage_ref")
    if passage_ref is not None and (not isinstance(passage_ref, str) or not passage_ref.strip()):
        raise NotebookError(f"{ctx}: passage_ref must be null or a non-empty string")
    notes = raw.get("notes", "")
    if not isinstance(notes, str):
        raise NotebookError(f"{ctx}: notes must be a string")

    return PracticeLogEntry(
        schema=schema,
        date=date,
        script_id=script_id,
        minutes=minutes,
        completed_steps=tuple(completed_steps),
        milestones_demonstrated=tuple(milestones),
        passage_ref=passage_ref,
        notes=notes,
    )


def load_practice_log(
    path: Path, catalog: ScriptCatalog | None = None
) -> tuple[PracticeLogEntry, ...]:
    cat = catalog or load_script_catalog()
    valid_scripts = set(cat.by_id())
    entries: list[PracticeLogEntry] = []
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise NotebookError(f"line {idx}: invalid JSON ({exc.msg})") from exc
        entries.append(parse_practice_log_entry(payload, line_no=idx, valid_scripts=valid_scripts))
    return tuple(entries)


def summarize_practice_log(entries: tuple[PracticeLogEntry, ...]) -> dict[str, Any]:
    by_script: dict[str, dict[str, Any]] = {}
    for entry in entries:
        bucket = by_script.setdefault(
            entry.script_id,
            {"sessions": 0, "minutes": 0, "milestones": set()},
        )
        bucket["sessions"] += 1
        bucket["minutes"] += entry.minutes
        bucket["milestones"].update(entry.milestones_demonstrated)

    formatted_scripts = {
        sid: {
            "sessions": data["sessions"],
            "minutes": data["minutes"],
            "milestones": sorted(data["milestones"]),
        }
        for sid, data in sorted(by_script.items())
    }
    return {
        "total_sessions": len(entries),
        "total_minutes": sum(e.minutes for e in entries),
        "scripts": formatted_scripts,
    }
