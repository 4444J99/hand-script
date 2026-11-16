"""Version-bound orthogonal script rendering records and editorial/permission gates."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hand_script.scripts import ScriptCatalog, load_script_catalog

EXPECTED_SCHEMA = "hand-script.rendering/1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

VALID_RENDERING_MODES = frozenset(
    {
        "character_transliteration",
        "phonetic_transcription",
        "calligraphic_treatment",
        "homophonic_adaptation",
        "invented_encoding",
        "translation",
    }
)
VALID_EDITORIAL_POOLS = frozenset({"active", "reserve", "study_only"})
VALID_REGISTRATION_STATUSES = frozenset({"unregistered", "pending", "registered"})
VALID_CLEARANCES = frozenset({"not_required", "pending", "granted", "withheld"})
VALID_PUBLIC_VISIBILITY = frozenset({"private", "staged", "public"})


class RenderingError(ValueError):
    """Raised when a rendering record violates schema or permission-axis rules."""


@dataclass(frozen=True)
class PermissionAxes:
    editorial_pool: str
    registration_status: str
    author_clearance: str
    collaborator_clearance: str
    public_visibility: str


@dataclass(frozen=True)
class ScriptRenderingRecord:
    schema: str
    rendering_id: str
    source_id: str
    source_version: str
    source_sha256: str
    target_script: str
    mode: str
    mapping_scheme: str
    rendered_text: str
    native_reader_reviewed: bool
    permissions: PermissionAxes
    notes: str = ""


@dataclass(frozen=True)
class RenderingAuditResult:
    rendering_id: str
    source_id: str
    is_stale: bool
    exportable_publicly: bool
    blockers: tuple[str, ...]


def _require_str(mapping: dict[str, Any], key: str, ctx: str) -> str:
    val = mapping.get(key)
    if not isinstance(val, str) or not val.strip():
        raise RenderingError(f"{ctx}: missing or empty string '{key}'")
    return val


def parse_rendering_record(
    raw: dict[str, Any],
    *,
    ctx: str = "rendering",
    valid_scripts: set[str] | None = None,
) -> ScriptRenderingRecord:
    if not isinstance(raw, dict):
        raise RenderingError(f"{ctx}: record must be a JSON object")
    schema = _require_str(raw, "schema", ctx)
    if schema != EXPECTED_SCHEMA:
        raise RenderingError(f"{ctx}: unsupported schema '{schema}' (expected '{EXPECTED_SCHEMA}')")
    rendering_id = _require_str(raw, "rendering_id", ctx)
    source_id = _require_str(raw, "source_id", ctx)
    source_version = _require_str(raw, "source_version", ctx)
    source_sha256 = _require_str(raw, "source_sha256", ctx)
    if not _SHA256_RE.match(source_sha256):
        raise RenderingError(f"{ctx}: invalid source_sha256 '{source_sha256}'")

    target_script = _require_str(raw, "target_script", ctx)
    if valid_scripts is not None and target_script not in valid_scripts:
        raise RenderingError(f"{ctx}: unknown target_script '{target_script}'")

    mode = _require_str(raw, "mode", ctx)
    if mode not in VALID_RENDERING_MODES:
        raise RenderingError(f"{ctx}: invalid mode '{mode}'")

    mapping_scheme = _require_str(raw, "mapping_scheme", ctx)
    rendered_text = _require_str(raw, "rendered_text", ctx)

    reviewed = raw.get("native_reader_reviewed")
    if not isinstance(reviewed, bool):
        raise RenderingError(f"{ctx}: native_reader_reviewed must be a boolean")

    perm_raw = raw.get("permissions")
    if not isinstance(perm_raw, dict):
        raise RenderingError(f"{ctx}: permissions must be an object")
    p_ctx = f"{ctx}.permissions"
    editorial_pool = _require_str(perm_raw, "editorial_pool", p_ctx)
    if editorial_pool not in VALID_EDITORIAL_POOLS:
        raise RenderingError(f"{p_ctx}: invalid editorial_pool '{editorial_pool}'")
    reg_status = _require_str(perm_raw, "registration_status", p_ctx)
    if reg_status not in VALID_REGISTRATION_STATUSES:
        raise RenderingError(f"{p_ctx}: invalid registration_status '{reg_status}'")
    author_cl = _require_str(perm_raw, "author_clearance", p_ctx)
    if author_cl not in VALID_CLEARANCES:
        raise RenderingError(f"{p_ctx}: invalid author_clearance '{author_cl}'")
    collab_cl = _require_str(perm_raw, "collaborator_clearance", p_ctx)
    if collab_cl not in VALID_CLEARANCES:
        raise RenderingError(f"{p_ctx}: invalid collaborator_clearance '{collab_cl}'")
    pub_vis = _require_str(perm_raw, "public_visibility", p_ctx)
    if pub_vis not in VALID_PUBLIC_VISIBILITY:
        raise RenderingError(f"{p_ctx}: invalid public_visibility '{pub_vis}'")

    notes = raw.get("notes", "")
    if not isinstance(notes, str):
        raise RenderingError(f"{ctx}: notes must be a string")

    return ScriptRenderingRecord(
        schema=schema,
        rendering_id=rendering_id,
        source_id=source_id,
        source_version=source_version,
        source_sha256=source_sha256,
        target_script=target_script,
        mode=mode,
        mapping_scheme=mapping_scheme,
        rendered_text=rendered_text,
        native_reader_reviewed=reviewed,
        permissions=PermissionAxes(
            editorial_pool=editorial_pool,
            registration_status=reg_status,
            author_clearance=author_cl,
            collaborator_clearance=collab_cl,
            public_visibility=pub_vis,
        ),
        notes=notes,
    )


def audit_rendering(
    record: ScriptRenderingRecord,
    *,
    current_source_hashes: dict[str, str] | None = None,
) -> RenderingAuditResult:
    """Evaluate version staleness and public-export eligibility.

    Enforces the five governance invariants from thread `3377c206`:
    1. Renderings bind to an exact `source_sha256`; source edits mark them stale.
    2. `editorial_pool == 'reserve'` or `'study_only'` never exports publicly.
    3. Author and collaborator clearances are checked independently of registration.
    4. `public_visibility` must explicitly equal `'public'`.
    5. Modes claiming natural-script legibility (`translation`,
       `calligraphic_treatment`, `character_transliteration`) require
       `native_reader_reviewed == True` before public export.
    """
    blockers: list[str] = []
    is_stale = False
    if current_source_hashes is not None and record.source_id in current_source_hashes:
        expected = current_source_hashes[record.source_id]
        if expected != record.source_sha256:
            is_stale = True
            blockers.append(
                f"stale rendering: bound to {record.source_sha256[:12]}..., "
                f"current source is {expected[:12]}..."
            )

    perms = record.permissions
    if perms.editorial_pool != "active":
        blockers.append(f"editorial_pool is '{perms.editorial_pool}' (must be 'active')")
    if perms.author_clearance not in {"granted", "not_required"}:
        blockers.append(f"author_clearance is '{perms.author_clearance}'")
    if perms.collaborator_clearance not in {"granted", "not_required"}:
        blockers.append(f"collaborator_clearance is '{perms.collaborator_clearance}'")
    if perms.public_visibility != "public":
        blockers.append(f"public_visibility is '{perms.public_visibility}'")

    if (
        record.mode
        in {
            "translation",
            "calligraphic_treatment",
            "character_transliteration",
        }
        and not record.native_reader_reviewed
    ):
        blockers.append(
            f"mode '{record.mode}' requires native_reader_reviewed=True before public export"
        )

    return RenderingAuditResult(
        rendering_id=record.rendering_id,
        source_id=record.source_id,
        is_stale=is_stale,
        exportable_publicly=(len(blockers) == 0),
        blockers=tuple(blockers),
    )


def load_renderings(
    path: Path, catalog: ScriptCatalog | None = None
) -> tuple[ScriptRenderingRecord, ...]:
    cat = catalog or load_script_catalog()
    valid_scripts = set(cat.by_id())
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise RenderingError("renderings file must contain a JSON array of records")
    seen_ids: set[str] = set()
    out: list[ScriptRenderingRecord] = []
    for idx, entry in enumerate(raw):
        rec = parse_rendering_record(entry, ctx=f"renderings[{idx}]", valid_scripts=valid_scripts)
        if rec.rendering_id in seen_ids:
            raise RenderingError(f"duplicate rendering_id '{rec.rendering_id}'")
        seen_ids.add(rec.rendering_id)
        out.append(rec)
    return tuple(out)
