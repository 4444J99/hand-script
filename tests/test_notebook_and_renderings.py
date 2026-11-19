"""Tests for the 6-step notebook session planner, practice logs, and rendering gates."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hand_script.notebook import (
    NotebookError,
    load_practice_log,
    plan_session,
    summarize_practice_log,
)
from hand_script.renderings import (
    RenderingError,
    audit_rendering,
    load_renderings,
    parse_rendering_record,
)


def test_session_plan_allocates_exact_minutes_across_six_steps() -> None:
    for target_minutes in (12, 15, 20, 35):
        plan = plan_session("arabic", minutes=target_minutes, passage_ref="FATIHA.1.1")
        assert len(plan.steps) == 6
        assert sum(s.minutes for s in plan.steps) == target_minutes
        assert plan.ruling == "abjad-rtl"
        assert plan.direction == "rtl"

    with pytest.raises(NotebookError, match="between 6 and 120"):
        plan_session("greek", minutes=3)


def test_practice_log_roundtrip_and_validation(tmp_path: Path) -> None:
    log_file = tmp_path / "sessions.jsonl"
    rows = [
        {
            "schema": "hand-script.practice-session/1",
            "date": "2026-11-15",
            "script_id": "greek",
            "minutes": 20,
            "completed_steps": [
                "warm_up",
                "copying",
                "memory_rewrite",
                "observation",
                "composition",
                "reflection",
            ],
            "milestones_demonstrated": ["inventory_recognition", "guided_copying"],
            "passage_ref": "ILIAD.1.1",
            "notes": "Practiced medial sigma vs final sigma.",
        },
        {
            "schema": "hand-script.practice-session/1",
            "date": "2026-11-16",
            "script_id": "kanji",
            "minutes": 15,
            "completed_steps": ["warm_up", "copying", "memory_rewrite"],
            "milestones_demonstrated": ["mapping_explanation"],
            "passage_ref": "DAODEJING.1.1",
            "notes": "Balanced 道 inside Tianzige box.",
        },
    ]
    log_file.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )
    entries = load_practice_log(log_file)
    summary = summarize_practice_log(entries)
    assert summary["total_sessions"] == 2
    assert summary["total_minutes"] == 35
    assert summary["scripts"]["greek"]["milestones"] == [
        "guided_copying",
        "inventory_recognition",
    ]

    bad_log = tmp_path / "bad.jsonl"
    bad_row = dict(rows[0], milestones_demonstrated=["percent_95_fluency"])
    bad_log.write_text(json.dumps(bad_row) + "\n", encoding="utf-8")
    with pytest.raises(NotebookError, match="unknown milestone"):
        load_practice_log(bad_log)


def test_rendering_audit_enforces_staleness_reserve_pool_and_review_gates(
    tmp_path: Path,
) -> None:
    sha_v1 = "a" * 64
    sha_v2 = "b" * 64

    clean_raw = {
        "schema": "hand-script.rendering/1",
        "rendering_id": "poem-001-greek-callig-v1",
        "source_id": "poem-001",
        "source_version": "1.0.0",
        "source_sha256": sha_v1,
        "target_script": "greek",
        "mode": "calligraphic_treatment",
        "mapping_scheme": "Attic-inspired phonetic adaptation",
        "rendered_text": "Μῆνιν ἄειδε",
        "native_reader_reviewed": True,
        "permissions": {
            "editorial_pool": "active",
            "registration_status": "registered",
            "author_clearance": "granted",
            "collaborator_clearance": "not_required",
            "public_visibility": "public",
        },
    }
    rec_clean = parse_rendering_record(clean_raw)
    res_ok = audit_rendering(rec_clean, current_source_hashes={"poem-001": sha_v1})
    assert res_ok.exportable_publicly
    assert not res_ok.is_stale
    assert res_ok.blockers == ()

    # Source hash edit triggers staleness blocker
    res_stale = audit_rendering(rec_clean, current_source_hashes={"poem-001": sha_v2})
    assert res_stale.is_stale
    assert not res_stale.exportable_publicly
    assert any("stale rendering" in b for b in res_stale.blockers)

    # Reserve pool + unreviewed translation + pending collaborator clearance all block export
    reserve_raw = {
        **clean_raw,
        "rendering_id": "poem-002-arabic-reserve",
        "source_id": "poem-002",
        "target_script": "arabic",
        "mode": "translation",
        "native_reader_reviewed": False,
        "permissions": {
            "editorial_pool": "reserve",
            "registration_status": "registered",
            "author_clearance": "granted",
            "collaborator_clearance": "pending",
            "public_visibility": "public",
        },
    }
    rec_reserve = parse_rendering_record(reserve_raw)
    res_blocked = audit_rendering(rec_reserve)
    assert not res_blocked.exportable_publicly
    assert any("editorial_pool is 'reserve'" in b for b in res_blocked.blockers)
    assert any("collaborator_clearance is 'pending'" in b for b in res_blocked.blockers)
    assert any("native_reader_reviewed=True" in b for b in res_blocked.blockers)

    # File loader rejects duplicate rendering_id
    dup_path = tmp_path / "renderings.json"
    dup_path.write_text(json.dumps([clean_raw, clean_raw]), encoding="utf-8")
    with pytest.raises(RenderingError, match="duplicate rendering_id"):
        load_renderings(dup_path)
