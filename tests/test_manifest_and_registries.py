"""Tests for project_manifest.json, scripts.json, languages.json, and linguistics_canon.json."""

from __future__ import annotations

import copy
import json
from importlib import resources
from pathlib import Path

import pytest

from hand_script.curriculum import (
    CurriculumError,
    load_language_map,
    load_linguistics_canon,
    parse_language_map,
    parse_linguistics_canon,
)
from hand_script.manifest import (
    ManifestError,
    load_manifest,
    parse_manifest,
    verify_preserved_copies,
)
from hand_script.scripts import (
    ScriptRegistryError,
    check_interference,
    load_script_catalog,
    parse_script_catalog,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_manifest_loads_and_verifies_preserved_docs() -> None:
    mf = load_manifest()
    assert mf.schema == "hand-script.manifest/1"
    assert mf.space.id == "053d129c-8941-4aa7-8dde-61aede81813d"
    assert len(mf.threads) == 12
    assert len(mf.external_exports) == 3

    verified = verify_preserved_copies(mf, REPO_ROOT)
    assert len(verified) == 3
    verified_paths = {rel for _, rel, _ in verified}
    assert "docs/perplexity/HS-M001-project-manifest.md" in verified_paths
    assert "docs/perplexity/HS-M001-inventory.json" in verified_paths
    assert "docs/perplexity/HS-F001-F002-preservation-report.md" in verified_paths


def test_manifest_implemented_modules_exist_and_import() -> None:
    mf = load_manifest()
    implemented = [c for c in mf.components if c.status == "implemented"]
    assert len(implemented) == 9
    for comp in implemented:
        assert comp.module is not None
        __import__(comp.module)


def test_manifest_rejects_bad_uuid_or_digest_mismatch(tmp_path: Path) -> None:
    raw = json.loads(
        resources.files("hand_script.data")
        .joinpath("project_manifest.json")
        .read_text(encoding="utf-8")
    )
    bad_uuid = copy.deepcopy(raw)
    bad_uuid["space"]["id"] = "NOT-A-LOWERCASE-UUID"
    with pytest.raises(ManifestError, match="UUID"):
        parse_manifest(bad_uuid)

    mf = parse_manifest(raw)
    doc = mf.imported_documents[0]
    fake_file = tmp_path / doc.path
    fake_file.parent.mkdir(parents=True, exist_ok=True)
    fake_file.write_text("tampered content\n", encoding="utf-8")
    with pytest.raises(ManifestError, match="sha256 mismatch"):
        verify_preserved_copies(mf, tmp_path)


def test_script_catalog_typologies_and_tracks() -> None:
    cat = load_script_catalog()
    assert len(cat.scripts) == 14
    ids = set(cat.by_id())
    assert {
        "latin",
        "greek",
        "cyrillic",
        "hebrew",
        "arabic",
        "hangul",
        "devanagari",
        "kana",
        "kanji",
    }.issubset(ids)

    kanji_stack = cat.get_track("kanji-first-stack")
    assert kanji_stack.scripts == ("latin", "cyrillic", "arabic", "kanji")
    greek_first = cat.get_track("greek-first-protocol")
    assert greek_first.scripts[0] == "greek"


def test_script_catalog_rejects_unknown_track_script() -> None:
    raw = json.loads(
        resources.files("hand_script.data").joinpath("scripts.json").read_text(encoding="utf-8")
    )
    broken = copy.deepcopy(raw)
    broken["tracks"]["kanji-first-stack"]["scripts"].append("klingon")
    with pytest.raises(ScriptRegistryError, match="unknown script 'klingon'"):
        parse_script_catalog(broken)


def test_interference_checks_flag_lookalikes_rtl_and_cap() -> None:
    # Greek + Cyrillic share bicameral lookalike group
    rep_gc = check_interference(["greek", "cyrillic"])
    assert "greco-roman-cyrillic-bicameral" in rep_gc.group_collisions
    assert len(rep_gc.warnings) >= 1

    # Hebrew + Arabic trigger concurrent RTL abjad warning
    rep_rtl = check_interference(["hebrew", "arabic"])
    assert "rtl-semitic-abjad-regime" in rep_rtl.group_collisions

    # Latin (baseline) + Arabic + Kanji stays within cap=2 with distinct regimes
    rep_clean = check_interference(["latin", "arabic", "kanji"])
    assert rep_clean.active_count == 2
    assert not rep_clean.exceeds_recommended_cap
    assert rep_clean.warnings == ()

    # Four active scripts exceed conservative cap=2
    rep_cap = check_interference(["greek", "arabic", "hangul", "devanagari"])
    assert rep_cap.exceeds_recommended_cap


def test_language_map_count_audit_and_chaucer_boundary() -> None:
    lmap = load_language_map()
    audit = lmap.count_audit()
    assert audit["turn6_core_languages"] == 16
    assert audit["archive_expansion_languages"] == 2
    assert audit["total_languages"] == 18
    assert audit["turn6_core_families"] == 9

    grc = lmap.filter_languages(script="greek")[0]
    pathway_ids = {p.id for p in grc.pathways}
    assert {"homeric", "koine-biblical"} == pathway_ids

    enm = next(lg for lg in lmap.languages if lg.id == "middle-english")
    assert "4444J99/chaucer" in enm.pathways[0].notes


def test_language_map_and_canon_validation_errors() -> None:
    raw_langs = json.loads(
        resources.files("hand_script.data").joinpath("languages.json").read_text(encoding="utf-8")
    )
    bad_langs = copy.deepcopy(raw_langs)
    bad_langs["languages"][0]["scripts"] = ["nonexistent-script"]
    with pytest.raises(CurriculumError, match="unknown script reference"):
        parse_language_map(bad_langs)

    canon = load_linguistics_canon()
    assert len(canon.works) >= 25
    ws_works = canon.filter_works(subfield="writing_systems")
    assert any(w.id == "daniels-bright-1996" for w in ws_works)

    raw_canon = json.loads(
        resources.files("hand_script.data")
        .joinpath("linguistics_canon.json")
        .read_text(encoding="utf-8")
    )
    bad_canon = copy.deepcopy(raw_canon)
    bad_canon["works"][0]["stage"] = "postdoctoral-mythic"
    with pytest.raises(CurriculumError, match="unknown stage"):
        parse_linguistics_canon(bad_canon)
