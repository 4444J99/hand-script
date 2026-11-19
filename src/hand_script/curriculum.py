"""Comparative 9-family language map and staged linguistics meta-canon."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from hand_script.scripts import ScriptCatalog, load_script_catalog

EXPECTED_LANGUAGES_SCHEMA = "hand-script.languages/1"
EXPECTED_CANON_SCHEMA = "hand-script.linguistics-canon/1"
VALID_ARCHIVE_STATUSES = frozenset({"turn6-core", "archive-expansion"})


class CurriculumError(ValueError):
    """Raised when `languages.json` or `linguistics_canon.json` fails validation."""


@dataclass(frozen=True)
class LanguageFamily:
    id: str
    name: str
    region: str


@dataclass(frozen=True)
class HistoricalPathway:
    id: str
    label: str
    founding_texts: tuple[str, ...]
    notes: str


@dataclass(frozen=True)
class LanguageEntry:
    id: str
    name: str
    family: str
    branch: str
    tier: int
    archive_status: str
    scripts: tuple[str, ...]
    pathways: tuple[HistoricalPathway, ...]


@dataclass(frozen=True)
class LanguageMap:
    schema: str
    source_note: str
    families: tuple[LanguageFamily, ...]
    languages: tuple[LanguageEntry, ...]

    def filter_languages(
        self,
        *,
        family: str | None = None,
        tier: int | None = None,
        script: str | None = None,
        archive_status: str | None = None,
    ) -> tuple[LanguageEntry, ...]:
        out: list[LanguageEntry] = []
        for lang in self.languages:
            if family is not None and lang.family != family:
                continue
            if tier is not None and lang.tier != tier:
                continue
            if script is not None and script not in lang.scripts:
                continue
            if archive_status is not None and lang.archive_status != archive_status:
                continue
            out.append(lang)
        return tuple(out)

    def count_audit(self) -> dict[str, int]:
        core = [lang for lang in self.languages if lang.archive_status == "turn6-core"]
        expansion = [lang for lang in self.languages if lang.archive_status == "archive-expansion"]
        core_families = {lang.family for lang in core}
        return {
            "total_languages": len(self.languages),
            "turn6_core_languages": len(core),
            "archive_expansion_languages": len(expansion),
            "turn6_core_families": len(core_families),
            "total_families": len(self.families),
        }


@dataclass(frozen=True)
class CanonWork:
    id: str
    authors: str
    title: str
    year: int
    subfield: str
    stage: str
    focus: str


@dataclass(frozen=True)
class LinguisticsCanon:
    schema: str
    caveat: str
    stages: tuple[str, ...]
    subfields: tuple[str, ...]
    works: tuple[CanonWork, ...]

    def filter_works(
        self, *, stage: str | None = None, subfield: str | None = None
    ) -> tuple[CanonWork, ...]:
        if stage is not None and stage not in self.stages:
            raise CurriculumError(
                f"unknown stage '{stage}' (expected one of {', '.join(self.stages)})"
            )
        if subfield is not None and subfield not in self.subfields:
            raise CurriculumError(
                f"unknown subfield '{subfield}' (expected one of {', '.join(self.subfields)})"
            )
        return tuple(
            work
            for work in self.works
            if (stage is None or work.stage == stage)
            and (subfield is None or work.subfield == subfield)
        )


def _require_str(mapping: dict[str, Any], key: str, ctx: str) -> str:
    val = mapping.get(key)
    if not isinstance(val, str) or not val.strip():
        raise CurriculumError(f"{ctx}: missing or empty string '{key}'")
    return val


def parse_language_map(
    raw: dict[str, Any], script_catalog: ScriptCatalog | None = None
) -> LanguageMap:
    if not isinstance(raw, dict):
        raise CurriculumError("languages root must be a JSON object")
    schema = _require_str(raw, "schema", "languages")
    if schema != EXPECTED_LANGUAGES_SCHEMA:
        raise CurriculumError(
            f"languages: unsupported schema '{schema}' (expected '{EXPECTED_LANGUAGES_SCHEMA}')"
        )
    source_note = _require_str(raw, "source_note", "languages")
    catalog = script_catalog or load_script_catalog()
    valid_scripts = set(catalog.by_id())

    families_raw = raw.get("families")
    if not isinstance(families_raw, list) or not families_raw:
        raise CurriculumError("languages.families must be a non-empty list")
    seen_families: set[str] = set()
    families: list[LanguageFamily] = []
    for idx, entry in enumerate(families_raw):
        ctx = f"families[{idx}]"
        if not isinstance(entry, dict):
            raise CurriculumError(f"{ctx} must be an object")
        fid = _require_str(entry, "id", ctx)
        if fid in seen_families:
            raise CurriculumError(f"{ctx}: duplicate family id '{fid}'")
        seen_families.add(fid)
        families.append(
            LanguageFamily(
                id=fid,
                name=_require_str(entry, "name", ctx),
                region=_require_str(entry, "region", ctx),
            )
        )

    languages_raw = raw.get("languages")
    if not isinstance(languages_raw, list) or not languages_raw:
        raise CurriculumError("languages.languages must be a non-empty list")
    seen_langs: set[str] = set()
    languages: list[LanguageEntry] = []
    for idx, entry in enumerate(languages_raw):
        ctx = f"languages[{idx}]"
        if not isinstance(entry, dict):
            raise CurriculumError(f"{ctx} must be an object")
        lid = _require_str(entry, "id", ctx)
        if lid in seen_langs:
            raise CurriculumError(f"{ctx}: duplicate language id '{lid}'")
        seen_langs.add(lid)
        fam = _require_str(entry, "family", ctx)
        if fam not in seen_families:
            raise CurriculumError(f"{ctx}: unknown family '{fam}'")
        tier = entry.get("tier")
        if not isinstance(tier, int) or tier not in {1, 2, 3}:
            raise CurriculumError(f"{ctx}: tier must be 1, 2, or 3")
        archive_status = _require_str(entry, "archive_status", ctx)
        if archive_status not in VALID_ARCHIVE_STATUSES:
            raise CurriculumError(f"{ctx}: invalid archive_status '{archive_status}'")
        scripts_raw = entry.get("scripts")
        if not isinstance(scripts_raw, list) or not scripts_raw:
            raise CurriculumError(f"{ctx}: scripts must be a non-empty list")
        scripts: list[str] = []
        for sid in scripts_raw:
            if not isinstance(sid, str) or sid not in valid_scripts:
                raise CurriculumError(f"{ctx}: unknown script reference '{sid}'")
            scripts.append(sid)

        pathways_raw = entry.get("pathways")
        if not isinstance(pathways_raw, list) or not pathways_raw:
            raise CurriculumError(f"{ctx}: pathways must be a non-empty list")
        pathways: list[HistoricalPathway] = []
        for p_idx, p_entry in enumerate(pathways_raw):
            p_ctx = f"{ctx}.pathways[{p_idx}]"
            if not isinstance(p_entry, dict):
                raise CurriculumError(f"{p_ctx} must be an object")
            texts_raw = p_entry.get("founding_texts")
            if (
                not isinstance(texts_raw, list)
                or not texts_raw
                or not all(isinstance(t, str) and t.strip() for t in texts_raw)
            ):
                raise CurriculumError(f"{p_ctx}: founding_texts must be a non-empty string list")
            pathways.append(
                HistoricalPathway(
                    id=_require_str(p_entry, "id", p_ctx),
                    label=_require_str(p_entry, "label", p_ctx),
                    founding_texts=tuple(texts_raw),
                    notes=_require_str(p_entry, "notes", p_ctx),
                )
            )

        languages.append(
            LanguageEntry(
                id=lid,
                name=_require_str(entry, "name", ctx),
                family=fam,
                branch=_require_str(entry, "branch", ctx),
                tier=tier,
                archive_status=archive_status,
                scripts=tuple(scripts),
                pathways=tuple(pathways),
            )
        )

    return LanguageMap(
        schema=schema,
        source_note=source_note,
        families=tuple(families),
        languages=tuple(languages),
    )


def load_language_map(
    path: Path | None = None, script_catalog: ScriptCatalog | None = None
) -> LanguageMap:
    if path is None:
        raw_text = (
            resources.files("hand_script.data")
            .joinpath("languages.json")
            .read_text(encoding="utf-8")
        )
    else:
        raw_text = path.read_text(encoding="utf-8")
    return parse_language_map(json.loads(raw_text), script_catalog=script_catalog)


def parse_linguistics_canon(raw: dict[str, Any]) -> LinguisticsCanon:
    if not isinstance(raw, dict):
        raise CurriculumError("canon root must be a JSON object")
    schema = _require_str(raw, "schema", "canon")
    if schema != EXPECTED_CANON_SCHEMA:
        raise CurriculumError(
            f"canon: unsupported schema '{schema}' (expected '{EXPECTED_CANON_SCHEMA}')"
        )
    caveat = _require_str(raw, "caveat", "canon")

    stages_raw = raw.get("stages")
    if (
        not isinstance(stages_raw, list)
        or not stages_raw
        or not all(isinstance(s, str) and s.strip() for s in stages_raw)
    ):
        raise CurriculumError("canon.stages must be a non-empty list of strings")
    stages = tuple(stages_raw)

    subfields_raw = raw.get("subfields")
    if (
        not isinstance(subfields_raw, list)
        or not subfields_raw
        or not all(isinstance(s, str) and s.strip() for s in subfields_raw)
    ):
        raise CurriculumError("canon.subfields must be a non-empty list of strings")
    subfields = tuple(subfields_raw)

    works_raw = raw.get("works")
    if not isinstance(works_raw, list) or not works_raw:
        raise CurriculumError("canon.works must be a non-empty list")

    seen_ids: set[str] = set()
    works: list[CanonWork] = []
    for idx, entry in enumerate(works_raw):
        ctx = f"works[{idx}]"
        if not isinstance(entry, dict):
            raise CurriculumError(f"{ctx} must be an object")
        wid = _require_str(entry, "id", ctx)
        if wid in seen_ids:
            raise CurriculumError(f"{ctx}: duplicate work id '{wid}'")
        seen_ids.add(wid)
        year = entry.get("year")
        if not isinstance(year, int) or year < 1800 or year > 2100:
            raise CurriculumError(f"{ctx}: invalid publication year '{year}'")
        subfield = _require_str(entry, "subfield", ctx)
        if subfield not in subfields:
            raise CurriculumError(f"{ctx}: unknown subfield '{subfield}'")
        stage = _require_str(entry, "stage", ctx)
        if stage not in stages:
            raise CurriculumError(f"{ctx}: unknown stage '{stage}'")
        works.append(
            CanonWork(
                id=wid,
                authors=_require_str(entry, "authors", ctx),
                title=_require_str(entry, "title", ctx),
                year=year,
                subfield=subfield,
                stage=stage,
                focus=_require_str(entry, "focus", ctx),
            )
        )

    return LinguisticsCanon(
        schema=schema,
        caveat=caveat,
        stages=stages,
        subfields=subfields,
        works=tuple(works),
    )


def load_linguistics_canon(path: Path | None = None) -> LinguisticsCanon:
    if path is None:
        raw_text = (
            resources.files("hand_script.data")
            .joinpath("linguistics_canon.json")
            .read_text(encoding="utf-8")
        )
    else:
        raw_text = path.read_text(encoding="utf-8")
    return parse_linguistics_canon(json.loads(raw_text))
