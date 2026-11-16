"""Tests for deterministic HTML sheet rendering, SVG geometry, and CLI subcommands."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from hand_script.atlas import render_atlas
from hand_script.cli import main
from hand_script.practice import (
    render_glyph_sheet,
    render_practice_sheet,
    render_ruling_svg,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SHEETS_DIR = REPO_ROOT / "sheets"


def test_committed_sheets_are_byte_identical_and_valid_svg() -> None:
    expected = {
        "greek_alphabet.glyph.html": render_glyph_sheet("greek"),
        "kanji_radicals.glyph.html": render_glyph_sheet("kanji"),
        "arabic_abjad.glyph.html": render_glyph_sheet("arabic"),
        "devanagari_abugida.glyph.html": render_glyph_sheet("devanagari"),
        "opening_passages.practice.html": render_practice_sheet(),
        "hand_script_atlas.html": render_atlas(),
    }
    for filename, fresh_html in expected.items():
        committed_path = SHEETS_DIR / filename
        assert committed_path.is_file(), f"missing committed sheet {filename}"
        assert committed_path.read_text(encoding="utf-8") == fresh_html
        # Ensure zero external network dependencies or scripts
        assert "<script" not in fresh_html.lower()
        assert "https://fonts.googleapis" not in fresh_html
        for svg in re.findall(r"<svg\b.*?</svg>", fresh_html, flags=re.DOTALL):
            ET.fromstring(svg)


def test_ruling_geometries_preserve_script_specific_cues() -> None:
    # Square grid strips ASCII wrapper punctuation so boxes hold only glyphs
    sq = render_ruling_svg("square-grid", trace_text="人 (亻)", boxes_per_row=4)
    assert ">人<" in sq
    assert ">亻<" in sq
    assert ">(" not in sq

    # RTL abjad aligns trace text to right edge without bidi-override distortion
    rtl = render_ruling_svg("abjad-rtl", trace_text="سَلَام")
    assert 'direction="rtl"' in rtl
    assert 'text-anchor="end"' in rtl
    assert "bidi-override" not in rtl

    # Head-line includes heavier shirorekha stroke
    hl = render_ruling_svg("head-line", trace_text="अग्नि")
    assert 'stroke-width="1.35"' in hl


def test_cli_subcommands_emit_valid_json(capsys, tmp_path: Path) -> None:
    assert main(["manifest", "--repo-root", str(REPO_ROOT), "--json"]) == 0
    mf_out = json.loads(capsys.readouterr().out)
    assert mf_out["threads"] == 12
    assert len(mf_out["verified_preserved_files"]) == 3

    assert main(["scripts", "--track", "kanji-first-stack", "--json"]) == 0
    tr_out = json.loads(capsys.readouterr().out)
    assert tr_out["scripts"] == ["latin", "cyrillic", "arabic", "kanji"]

    assert main(["check-interference", "greek", "cyrillic", "--json"]) == 0
    inter_out = json.loads(capsys.readouterr().out)
    assert "greco-roman-cyrillic-bicameral" in inter_out["group_collisions"]

    assert main(["inspect-text", "שָׁלוֹם", "--json"]) == 0
    insp_out = json.loads(capsys.readouterr().out)
    assert len(insp_out) == 4

    assert main(["languages", "--status", "turn6-core", "--json"]) == 0
    lang_out = json.loads(capsys.readouterr().out)
    assert len(lang_out["languages"]) == 16

    assert main(["canon", "--stage", "graduate", "--json"]) == 0
    canon_out = json.loads(capsys.readouterr().out)
    assert len(canon_out["works"]) >= 8

    assert main(["network", "--cluster", "word-speech-way", "--json"]) == 0
    net_out = json.loads(capsys.readouterr().out)
    assert any(edge["relation"] == "translation" for edge in net_out)

    assert main(["plan-session", "devanagari", "--minutes", "18", "--json"]) == 0
    plan_out = json.loads(capsys.readouterr().out)
    assert sum(step["minutes"] for step in plan_out["steps"]) == 18

    out_sheet = tmp_path / "iliad_only.html"
    assert main(["practice-sheet", "--ref", "ILIAD.1.1", "-o", str(out_sheet)]) == 0
    assert "Μῆνιν ἄειδε" in out_sheet.read_text(encoding="utf-8")


def test_cli_check_log_and_check_renderings_and_human_modes(capsys, tmp_path: Path) -> None:
    log_path = tmp_path / "log.jsonl"
    log_path.write_text(
        json.dumps(
            {
                "schema": "hand-script.practice-session/1",
                "date": "2026-11-15",
                "script_id": "hebrew",
                "minutes": 20,
                "completed_steps": ["warm_up", "copying", "reflection"],
                "milestones_demonstrated": ["delayed_readback"],
                "passage_ref": "GENESIS.1.1",
                "notes": "Checked final mem vs samekh.",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert main(["check-log", str(log_path)]) == 0
    assert "delayed_readback" in capsys.readouterr().out

    sha = "c" * 64
    rend_path = tmp_path / "rend.json"
    rend_path.write_text(
        json.dumps(
            [
                {
                    "schema": "hand-script.rendering/1",
                    "rendering_id": "r-1",
                    "source_id": "poem-7",
                    "source_version": "1",
                    "source_sha256": sha,
                    "target_script": "hangul",
                    "mode": "phonetic_transcription",
                    "mapping_scheme": "IPA-to-Hangul syllable approximation",
                    "rendered_text": "한글",
                    "native_reader_reviewed": False,
                    "permissions": {
                        "editorial_pool": "active",
                        "registration_status": "registered",
                        "author_clearance": "granted",
                        "collaborator_clearance": "not_required",
                        "public_visibility": "public",
                    },
                }
            ]
        ),
        encoding="utf-8",
    )
    sources_path = tmp_path / "sources.json"
    sources_path.write_text(json.dumps({"poem-7": sha}), encoding="utf-8")
    assert (
        main(
            [
                "check-renderings",
                str(rend_path),
                "--sources-json",
                str(sources_path),
            ]
        )
        == 0
    )
    assert "EXPORTABLE" in capsys.readouterr().out

    # Exercise human-readable text output modes across subcommands
    assert main(["manifest", "--repo-root", str(REPO_ROOT)]) == 0
    assert main(["scripts"]) == 0
    assert main(["languages", "--family", "uralic"]) == 0
    assert main(["canon", "--subfield", "writing_systems"]) == 0
    assert main(["network", "--cluster", "tree-root-radical"]) == 0
    assert main(["plan-session", "greek", "--minutes", "15"]) == 0
    capsys.readouterr()
