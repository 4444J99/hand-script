"""Writing-system typology, script inventory, and similarity-interference checks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

EXPECTED_SCHEMA = "hand-script.scripts/1"

VALID_TYPOLOGIES = frozenset(
    {"alphabet", "abjad", "abugida", "syllabary", "morphographic", "featural"}
)
VALID_DIRECTIONS = frozenset({"ltr", "rtl"})
VALID_RULINGS = frozenset({"four-line", "abjad-rtl", "head-line", "square-grid"})


class ScriptRegistryError(ValueError):
    """Raised when `scripts.json` fails structural or typological validation."""


@dataclass(frozen=True)
class ExemplarGlyph:
    glyph: str
    name: str
    value: str
    form_note: str


@dataclass(frozen=True)
class ScriptSpec:
    id: str
    name: str
    typology: str
    direction: str
    ruling: str
    interference_group: str
    unicode_blocks: tuple[str, ...]
    inventory_summary: str
    encoded_unit: str
    cognitive_regime: str
    ductus_notes: str
    exemplars: tuple[ExemplarGlyph, ...]


@dataclass(frozen=True)
class SequencingTrack:
    id: str
    source: str
    description: str
    scripts: tuple[str, ...]


@dataclass(frozen=True)
class InterferenceReport:
    selected_scripts: tuple[str, ...]
    active_count: int
    group_collisions: dict[str, tuple[str, ...]]
    exceeds_recommended_cap: bool
    warnings: tuple[str, ...]
    epistemic_note: str


@dataclass(frozen=True)
class ScriptCatalog:
    schema: str
    typology_authority: str
    sequencing_note: str
    tracks: tuple[SequencingTrack, ...]
    scripts: tuple[ScriptSpec, ...]

    def by_id(self) -> dict[str, ScriptSpec]:
        return {script.id: script for script in self.scripts}

    def get_script(self, script_id: str) -> ScriptSpec:
        lookup = self.by_id()
        if script_id not in lookup:
            known = ", ".join(sorted(lookup))
            raise KeyError(f"unknown script '{script_id}' (known: {known})")
        return lookup[script_id]

    def get_track(self, track_id: str) -> SequencingTrack:
        for track in self.tracks:
            if track.id == track_id:
                return track
        known = ", ".join(t.id for t in self.tracks)
        raise KeyError(f"unknown track '{track_id}' (known: {known})")


def _require_str(mapping: dict[str, Any], key: str, ctx: str) -> str:
    val = mapping.get(key)
    if not isinstance(val, str) or not val.strip():
        raise ScriptRegistryError(f"{ctx}: missing or empty string '{key}'")
    return val


def _require_str_list(mapping: dict[str, Any], key: str, ctx: str) -> tuple[str, ...]:
    val = mapping.get(key)
    if (
        not isinstance(val, list)
        or not val
        or not all(isinstance(item, str) and item.strip() for item in val)
    ):
        raise ScriptRegistryError(f"{ctx}: '{key}' must be a non-empty list of strings")
    return tuple(val)


def parse_script_catalog(raw: dict[str, Any]) -> ScriptCatalog:
    if not isinstance(raw, dict):
        raise ScriptRegistryError("scripts root must be a JSON object")
    schema = _require_str(raw, "schema", "scripts")
    if schema != EXPECTED_SCHEMA:
        raise ScriptRegistryError(
            f"scripts: unsupported schema '{schema}' (expected '{EXPECTED_SCHEMA}')"
        )
    typology_authority = _require_str(raw, "typology_authority", "scripts")
    sequencing_note = _require_str(raw, "sequencing_note", "scripts")

    scripts_raw = raw.get("scripts")
    if not isinstance(scripts_raw, list) or not scripts_raw:
        raise ScriptRegistryError("scripts.scripts must be a non-empty list")

    seen_ids: set[str] = set()
    scripts: list[ScriptSpec] = []
    for idx, entry in enumerate(scripts_raw):
        ctx = f"scripts[{idx}]"
        if not isinstance(entry, dict):
            raise ScriptRegistryError(f"{ctx} must be an object")
        sid = _require_str(entry, "id", ctx)
        if sid in seen_ids:
            raise ScriptRegistryError(f"{ctx}: duplicate script id '{sid}'")
        seen_ids.add(sid)

        typology = _require_str(entry, "typology", ctx)
        if typology not in VALID_TYPOLOGIES:
            raise ScriptRegistryError(f"{ctx}: invalid typology '{typology}'")
        direction = _require_str(entry, "direction", ctx)
        if direction not in VALID_DIRECTIONS:
            raise ScriptRegistryError(f"{ctx}: invalid direction '{direction}'")
        ruling = _require_str(entry, "ruling", ctx)
        if ruling not in VALID_RULINGS:
            raise ScriptRegistryError(f"{ctx}: invalid ruling '{ruling}'")

        exemplars_raw = entry.get("exemplars")
        if not isinstance(exemplars_raw, list) or not exemplars_raw:
            raise ScriptRegistryError(f"{ctx}: exemplars must be non-empty")
        exemplars: list[ExemplarGlyph] = []
        for g_idx, g_entry in enumerate(exemplars_raw):
            g_ctx = f"{ctx}.exemplars[{g_idx}]"
            if not isinstance(g_entry, dict):
                raise ScriptRegistryError(f"{g_ctx} must be an object")
            exemplars.append(
                ExemplarGlyph(
                    glyph=_require_str(g_entry, "glyph", g_ctx),
                    name=_require_str(g_entry, "name", g_ctx),
                    value=_require_str(g_entry, "value", g_ctx),
                    form_note=_require_str(g_entry, "form_note", g_ctx),
                )
            )

        scripts.append(
            ScriptSpec(
                id=sid,
                name=_require_str(entry, "name", ctx),
                typology=typology,
                direction=direction,
                ruling=ruling,
                interference_group=_require_str(entry, "interference_group", ctx),
                unicode_blocks=_require_str_list(entry, "unicode_blocks", ctx),
                inventory_summary=_require_str(entry, "inventory_summary", ctx),
                encoded_unit=_require_str(entry, "encoded_unit", ctx),
                cognitive_regime=_require_str(entry, "cognitive_regime", ctx),
                ductus_notes=_require_str(entry, "ductus_notes", ctx),
                exemplars=tuple(exemplars),
            )
        )

    tracks_raw = raw.get("tracks")
    if not isinstance(tracks_raw, dict) or not tracks_raw:
        raise ScriptRegistryError("scripts.tracks must be a non-empty object")

    tracks: list[SequencingTrack] = []
    for tid, entry in tracks_raw.items():
        ctx = f"tracks.{tid}"
        if not isinstance(entry, dict):
            raise ScriptRegistryError(f"{ctx} must be an object")
        seq = _require_str_list(entry, "scripts", ctx)
        for sid in seq:
            if sid not in seen_ids:
                raise ScriptRegistryError(f"{ctx}: track references unknown script '{sid}'")
        tracks.append(
            SequencingTrack(
                id=tid,
                source=_require_str(entry, "source", ctx),
                description=_require_str(entry, "description", ctx),
                scripts=seq,
            )
        )

    return ScriptCatalog(
        schema=schema,
        typology_authority=typology_authority,
        sequencing_note=sequencing_note,
        tracks=tuple(tracks),
        scripts=tuple(scripts),
    )


def load_script_catalog(path: Path | None = None) -> ScriptCatalog:
    if path is None:
        raw_text = (
            resources.files("hand_script.data").joinpath("scripts.json").read_text(encoding="utf-8")
        )
    else:
        raw_text = path.read_text(encoding="utf-8")
    return parse_script_catalog(json.loads(raw_text))


def check_interference(
    script_ids: list[str] | tuple[str, ...],
    catalog: ScriptCatalog | None = None,
    *,
    baseline_scripts: frozenset[str] = frozenset({"latin"}),
    recommended_active_cap: int = 2,
) -> InterferenceReport:
    """Check concurrent active script choices for structural/graphic interference.

    Follows HS-T003 and HS-F013: flags concurrent non-baseline scripts sharing an
    `interference_group` (e.g., Greek + Cyrillic + Cherokee false-friend shapes),
    concurrent RTL consonantal abjads (Hebrew + Arabic), or active script counts
    exceeding the conservative concurrency cap.
    """
    cat = catalog or load_script_catalog()
    deduped: list[str] = []
    for sid in script_ids:
        cat.get_script(sid)
        if sid not in deduped:
            deduped.append(sid)

    active = [sid for sid in deduped if sid not in baseline_scripts]
    groups: dict[str, list[str]] = {}
    rtl_abjads: list[str] = []
    for sid in deduped:
        spec = cat.get_script(sid)
        groups.setdefault(spec.interference_group, []).append(sid)
        if sid not in baseline_scripts and spec.direction == "rtl" and spec.typology == "abjad":
            rtl_abjads.append(sid)

    collisions: dict[str, tuple[str, ...]] = {}
    warnings: list[str] = []
    for group_name, members in sorted(groups.items()):
        non_baseline = [m for m in members if m not in baseline_scripts]
        if len(members) >= 2 and len(non_baseline) >= 2:
            collisions[group_name] = tuple(members)
            warnings.append(
                f"Group '{group_name}' has concurrent active scripts "
                f"({', '.join(members)}): high grapheme/phoneme lookalike "
                "remapping risk; stabilize one before adding the second."
            )

    if len(rtl_abjads) >= 2 and "rtl-semitic-abjad-regime" not in collisions:
        collisions["rtl-semitic-abjad-regime"] = tuple(rtl_abjads)
        warnings.append(
            f"Concurrent RTL consonantal abjads selected ({', '.join(rtl_abjads)}): "
            "high directional and root-template overlap during initial acquisition."
        )

    exceeds_cap = len(active) > recommended_active_cap
    if exceeds_cap:
        warnings.append(
            f"{len(active)} active non-baseline scripts selected "
            f"({', '.join(active)}), exceeding the conservative concurrency cap "
            f"of {recommended_active_cap} active acquisition scripts."
        )

    return InterferenceReport(
        selected_scripts=tuple(deduped),
        active_count=len(active),
        group_collisions=collisions,
        exceeds_recommended_cap=exceeds_cap,
        warnings=tuple(warnings),
        epistemic_note=(
            "Concurrency caps (2 conservative / 3 upper heuristic) and spacing "
            "windows in HS-T003 are practical scheduling heuristics derived from "
            "general memory/interference literature, not script-specific "
            "psychometric constants."
        ),
    )
