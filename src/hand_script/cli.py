"""Command-line interface (`hand-script`) for the script-learning workbench."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path

from hand_script import __version__, log, packet, scripts, sheets
from hand_script.atlas import render_atlas
from hand_script.curriculum import load_language_map, load_linguistics_canon
from hand_script.etymology import load_lexical_network
from hand_script.manifest import load_manifest, verify_preserved_copies
from hand_script.notebook import (
    load_practice_log,
    plan_session,
    summarize_practice_log,
)
from hand_script.practice import render_glyph_sheet, render_practice_sheet
from hand_script.renderings import audit_rendering, load_renderings
from hand_script.scripts import check_interference, load_script_catalog
from hand_script.unicode_inspect import inspect_text


def _write_output(content: str, output_path: Path | None) -> None:
    if output_path is None:
        sys.stdout.write(content)
        if not content.endswith("\n"):
            sys.stdout.write("\n")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")


def cmd_sheets(args: argparse.Namespace) -> int:
    ids = scripts.available() if args.script == "all" else [args.script]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for sid in ids:
        data = scripts.load(sid)
        for kind, fn in (("letters", sheets.letter_sheet), ("copy", sheets.copy_sheet)):
            path = out / f"{sid}-{kind}.html"
            path.write_text(fn(data), encoding="utf-8")
            print(path)
    return 0


def _log_path(args: argparse.Namespace) -> Path:
    return Path(args.file or os.environ.get("HAND_SCRIPT_LOG") or log.DEFAULT_PATH)


def cmd_log_add(args: argparse.Namespace) -> int:
    day = date.fromisoformat(args.date) if args.date else date.today()
    entry = log.make_entry(
        day, args.script, args.minutes, args.characters, args.lines, args.focus, args.note
    )
    log.append(_log_path(args), entry)
    print(f"logged {entry['script']} {entry['minutes']} min on {entry['date']}")
    return 0


def cmd_log_summary(args: argparse.Namespace) -> int:
    entries = log.read(_log_path(args))
    print(log.format_summary(log.summarize(entries, date.today())))
    return 0


def cmd_packet(args: argparse.Namespace) -> int:
    ids = scripts.available() if args.script == "all" else [args.script]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    entries = log.read(_log_path(args))
    today = date.fromisoformat(args.date) if args.date else date.today()
    for sid in ids:
        path = out / f"{sid}-week-{packet.monday_of(today).isoformat()}.html"
        path.write_text(packet.packet(scripts.load(sid), entries, today), encoding="utf-8")
        print(path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hand-script",
        description=(
            "Handwriting-centered script-learning, writing-system typology, "
            "and relationship-labeled etymology workbench."
        ),
    )
    parser.add_argument("--version", action="version", version=f"hand-script {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_manifest = sub.add_parser("manifest", help="Inspect and verify project manifest")
    p_manifest.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root used to verify SHA-256 hashes of docs/perplexity/* copies",
    )
    p_manifest.add_argument("--json", action="store_true", help="Emit JSON output")

    p_scripts = sub.add_parser("scripts", help="List writing systems or sequencing tracks")
    p_scripts.add_argument("--track", type=str, default=None, help="Sequencing track ID")
    p_scripts.add_argument("--json", action="store_true", help="Emit JSON output")

    p_interf = sub.add_parser(
        "check-interference",
        help="Check concurrent script selection for structural/graphic interference",
    )
    p_interf.add_argument("script_ids", nargs="+", help="Script IDs to check")
    p_interf.add_argument(
        "--cap",
        type=int,
        default=2,
        help="Conservative cap for concurrent non-baseline active scripts (default: 2)",
    )
    p_interf.add_argument("--json", action="store_true", help="Emit JSON output")

    p_inspect = sub.add_parser(
        "inspect-text", help="Inspect Unicode grapheme clusters and combining marks"
    )
    p_inspect.add_argument("text", type=str, help="Sample text to inspect")
    p_inspect.add_argument(
        "--skip-whitespace", action="store_true", help="Skip whitespace characters"
    )
    p_inspect.add_argument("--json", action="store_true", help="Emit JSON output")

    p_langs = sub.add_parser(
        "languages", help="Query the comparative language and founding-text map"
    )
    p_langs.add_argument("--family", type=str, default=None, help="Filter by family ID")
    p_langs.add_argument("--tier", type=int, default=None, help="Filter by tier (1-3)")
    p_langs.add_argument("--script", type=str, default=None, help="Filter by script ID")
    p_langs.add_argument(
        "--status",
        type=str,
        default=None,
        help="Filter by archive_status (turn6-core or archive-expansion)",
    )
    p_langs.add_argument("--json", action="store_true", help="Emit JSON output")

    p_canon = sub.add_parser("canon", help="Query the staged linguistics meta-canon")
    p_canon.add_argument(
        "--stage",
        type=str,
        default=None,
        help="Filter by stage (undergraduate, graduate, doctoral)",
    )
    p_canon.add_argument("--subfield", type=str, default=None, help="Filter by subfield")
    p_canon.add_argument("--json", action="store_true", help="Emit JSON output")

    p_net = sub.add_parser(
        "network", help="Inspect relationship-labeled lexical & translation clusters"
    )
    p_net.add_argument("--cluster", type=str, default=None, help="Concept cluster ID")
    p_net.add_argument("--relation", type=str, default=None, help="Edge relation filter")
    p_net.add_argument("--json", action="store_true", help="Emit JSON output")

    p_plan = sub.add_parser("plan-session", help="Generate a 6-step notebook practice session plan")
    p_plan.add_argument("script_id", type=str, help="Target script ID")
    p_plan.add_argument(
        "--minutes", type=int, default=20, help="Total session minutes (default: 20)"
    )
    p_plan.add_argument("--passage", type=str, default=None, help="Optional passage ref")
    p_plan.add_argument("--json", action="store_true", help="Emit JSON output")

    p_log = sub.add_parser(
        "check-log", help="Validate and summarize a JSONL handwriting practice log"
    )
    p_log.add_argument("log_path", type=Path, help="Path to JSONL practice log")
    p_log.add_argument("--json", action="store_true", help="Emit JSON output")

    p_rend = sub.add_parser(
        "check-renderings",
        help="Audit version-bound script renderings for staleness and export gates",
    )
    p_rend.add_argument("renderings_path", type=Path, help="Path to renderings JSON array")
    p_rend.add_argument(
        "--sources-json",
        type=Path,
        default=None,
        help="Optional JSON mapping {source_id: current_sha256}",
    )
    p_rend.add_argument("--json", action="store_true", help="Emit JSON output")

    p_glyph = sub.add_parser(
        "glyph-sheet", help="Render a deterministic printable HTML exemplar glyph sheet"
    )
    p_glyph.add_argument("script_id", type=str, help="Script ID")
    p_glyph.add_argument(
        "--boxes", type=int, default=10, help="Boxes per row on square-grid sheets"
    )
    p_glyph.add_argument("-o", "--output", type=Path, default=None, help="Output HTML path")

    p_prac = sub.add_parser(
        "practice-sheet",
        help="Render a deterministic printable HTML canonical passage practice sheet",
    )
    p_prac.add_argument(
        "--ref",
        action="append",
        default=None,
        help="Passage ref to include (repeatable; omit to include all)",
    )
    p_prac.add_argument(
        "--rows", type=int, default=2, help="Practice ruling rows per passage (1-5)"
    )
    p_prac.add_argument("-o", "--output", type=Path, default=None, help="Output HTML path")

    p_atlas = sub.add_parser(
        "render-atlas", help="Render the standalone HTML comparative script & root atlas"
    )
    p_atlas.add_argument("-o", "--output", type=Path, default=None, help="Output HTML path")

    # Practice sheets / log / weekly packet (from main's sheets-log-packet layer).
    s = sub.add_parser("sheets", help="write printable practice sheets (HTML)")
    s.add_argument("script", help="script id or 'all'")
    s.add_argument("--out", default="sheets")
    s.set_defaults(fn=cmd_sheets)
    pk = sub.add_parser("packet", help="weekly packet: progress summary + graded daily drills")
    pk.add_argument("script", help="script id or 'all'")
    pk.add_argument("--out", default="packets")
    pk.add_argument("--file", help="log path")
    pk.add_argument("--date", help="any day in the target week, YYYY-MM-DD (default today)")
    pk.set_defaults(fn=cmd_packet)
    lg = sub.add_parser("log", help="practice log")
    lg.add_argument("--file", help="log path (default data/practice-log.jsonl or $HAND_SCRIPT_LOG)")
    ls = lg.add_subparsers(dest="log_cmd", required=True)
    a = ls.add_parser("add", help="record a practice sitting")
    a.add_argument("script")
    a.add_argument("--minutes", type=int, default=0)
    a.add_argument("--characters", type=int, default=0)
    a.add_argument("--lines", type=int, default=0)
    a.add_argument("--focus", default="")
    a.add_argument("--note", default="")
    a.add_argument("--date", help="YYYY-MM-DD (default today)")
    a.set_defaults(fn=cmd_log_add)
    sm = ls.add_parser("summary", help="totals, per-script, streaks")
    sm.set_defaults(fn=cmd_log_summary)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Commands registered with an fn (sheets / packet / log) dispatch directly.
    fn = getattr(args, "fn", None)
    if fn is not None:
        try:
            return fn(args)
        except KeyError as e:
            print(f"error: {e.args[0]}")
            return 2
        except ValueError as e:
            print(f"error: {e}")
            return 2

    if args.command == "manifest":
        mf = load_manifest()
        verified: list[tuple[str, str, str]] = []
        if args.repo_root is not None:
            verified = verify_preserved_copies(mf, args.repo_root)
        summary = mf.summary_counts()
        if verified:
            summary["verified_preserved_files"] = [
                {"id": aid, "path": rel, "sha256": digest} for aid, rel, digest in verified
            ]
        if args.json:
            _write_output(json.dumps(summary, indent=2, sort_keys=True), None)
        else:
            lines = [
                f"{mf.project} ({mf.schema}) — Space {mf.space.id}",
                f"Threads: {summary['threads']} | External exports: "
                f"{summary['external_exports']} | Imported docs: "
                f"{summary['imported_documents']}",
                f"Components ({summary['components']}): "
                + ", ".join(f"{k}={v}" for k, v in sorted(summary["components_by_status"].items())),
            ]
            if verified:
                lines.append(f"Verified SHA-256 digests: {len(verified)}/{len(verified)} OK")
            _write_output("\n".join(lines), None)
        return 0

    if args.command == "scripts":
        cat = load_script_catalog()
        if args.track:
            track = cat.get_track(args.track)
            if args.json:
                _write_output(json.dumps(asdict(track), indent=2), None)
            else:
                seq_str = " -> ".join(track.scripts)
                _write_output(
                    f"{track.id} [{track.source}]\nOrder: {seq_str}\n{track.description}",
                    None,
                )
            return 0
        if args.json:
            _write_output(
                json.dumps([asdict(s) for s in cat.scripts], indent=2, ensure_ascii=False),
                None,
            )
        else:
            lines = [
                f"{s.id:12s}  {s.typology:14s}  {s.direction:4s}  {s.ruling:11s}  {s.name}"
                for s in cat.scripts
            ]
            _write_output("\n".join(lines), None)
        return 0

    if args.command == "check-interference":
        report = check_interference(args.script_ids, recommended_active_cap=args.cap)
        if args.json:
            _write_output(json.dumps(asdict(report), indent=2), None)
        else:
            lines = [
                f"Selected scripts: {', '.join(report.selected_scripts)} "
                f"(active non-baseline: {report.active_count})"
            ]
            if report.warnings:
                for warn in report.warnings:
                    lines.append(f"WARNING: {warn}")
            else:
                lines.append("OK: no structural group collisions or concurrency cap warnings.")
            lines.append(f"Note: {report.epistemic_note}")
            _write_output("\n".join(lines), None)
        return 0

    if args.command == "inspect-text":
        clusters = inspect_text(args.text, skip_whitespace=args.skip_whitespace)
        if args.json:
            _write_output(
                json.dumps([asdict(c) for c in clusters], indent=2, ensure_ascii=False),
                None,
            )
        else:
            lines = []
            for cl in clusters:
                marks_desc = ", ".join(f"{m.codepoint} {m.name}" for m in cl.marks)
                suffix = f" + [{marks_desc}]" if marks_desc else ""
                lines.append(
                    f"{cl.surface}\t{cl.base.codepoint} {cl.base.name} "
                    f"(cat={cl.base.category}, bidi={cl.base.bidirectional}){suffix}"
                )
            _write_output("\n".join(lines), None)
        return 0

    if args.command == "languages":
        lmap = load_language_map()
        entries = lmap.filter_languages(
            family=args.family,
            tier=args.tier,
            script=args.script,
            archive_status=args.status,
        )
        if args.json:
            payload = {
                "audit": lmap.count_audit(),
                "languages": [asdict(e) for e in entries],
            }
            _write_output(json.dumps(payload, indent=2, ensure_ascii=False), None)
        else:
            audit = lmap.count_audit()
            lines = [
                f"Audit: {audit['turn6_core_languages']} Turn-6 core languages + "
                f"{audit['archive_expansion_languages']} archive expansions "
                f"({len(entries)} matched)"
            ]
            for e in entries:
                lines.append(
                    f"- {e.id} ({e.name}) | family={e.family} | tier={e.tier} | "
                    f"status={e.archive_status} | scripts={','.join(e.scripts)}"
                )
            _write_output("\n".join(lines), None)
        return 0

    if args.command == "canon":
        canon = load_linguistics_canon()
        works = canon.filter_works(stage=args.stage, subfield=args.subfield)
        if args.json:
            _write_output(
                json.dumps(
                    {"caveat": canon.caveat, "works": [asdict(w) for w in works]},
                    indent=2,
                ),
                None,
            )
        else:
            lines = [f"Caveat: {canon.caveat}", f"Matched works: {len(works)}"]
            for wk in works:
                lines.append(f"- [{wk.stage}/{wk.subfield}] {wk.authors} ({wk.year}), {wk.title}")
            _write_output("\n".join(lines), None)
        return 0

    if args.command == "network":
        net = load_lexical_network()
        nodes_lookup = net.nodes_by_id()
        if args.cluster:
            edges = net.get_cluster_edges(args.cluster, relation=args.relation)
        else:
            edges = tuple(
                e for e in net.edges if args.relation is None or e.relation == args.relation
            )
        if args.json:
            _write_output(
                json.dumps([asdict(e) for e in edges], indent=2, ensure_ascii=False),
                None,
            )
        else:
            lines = [f"Matched edges: {len(edges)}"]
            for e in edges:
                src = nodes_lookup[e.source]
                tgt = nodes_lookup[e.target]
                lines.append(
                    f"- [{e.cluster} | {e.relation}] {src.form} ({src.language}) -> "
                    f"{tgt.form} ({tgt.language}): {e.evidence}"
                )
            _write_output("\n".join(lines), None)
        return 0

    if args.command == "plan-session":
        plan = plan_session(args.script_id, minutes=args.minutes, passage_ref=args.passage)
        if args.json:
            _write_output(json.dumps(asdict(plan), indent=2, ensure_ascii=False), None)
        else:
            lines = [
                f"Session Plan — {plan.script_name} ({plan.total_minutes} min, "
                f"ruling={plan.ruling}, dir={plan.direction})",
                f"Focus glyphs: {' '.join(plan.focus_glyphs)}",
            ]
            if plan.passage_ref:
                lines.append(f"Passage: {plan.passage_ref}")
            for idx, st in enumerate(plan.steps, start=1):
                lines.append(f"  {idx}. {st.step_id} ({st.minutes} min): {st.instruction}")
            lines.append(f"Scope note: {plan.scope_note}")
            _write_output("\n".join(lines), None)
        return 0

    if args.command == "check-log":
        entries = load_practice_log(args.log_path)
        summary = summarize_practice_log(entries)
        if args.json:
            _write_output(json.dumps(summary, indent=2, sort_keys=True), None)
        else:
            lines = [
                f"Sessions: {summary['total_sessions']} | Total minutes: {summary['total_minutes']}"
            ]
            for sid, data in summary["scripts"].items():
                ms = ", ".join(data["milestones"]) or "none yet"
                lines.append(
                    f"- {sid}: {data['sessions']} sessions, {data['minutes']} min "
                    f"(milestones: {ms})"
                )
            _write_output("\n".join(lines), None)
        return 0

    if args.command == "check-renderings":
        records = load_renderings(args.renderings_path)
        source_hashes: dict[str, str] | None = None
        if args.sources_json is not None:
            source_hashes = json.loads(args.sources_json.read_text(encoding="utf-8"))
        results = [audit_rendering(rec, current_source_hashes=source_hashes) for rec in records]
        if args.json:
            _write_output(json.dumps([asdict(r) for r in results], indent=2), None)
        else:
            lines = []
            for r in results:
                state = "EXPORTABLE" if r.exportable_publicly else "BLOCKED"
                detail = "; ".join(r.blockers) if r.blockers else "all gates satisfied"
                lines.append(f"{r.rendering_id} ({r.source_id}): {state} — {detail}")
            _write_output("\n".join(lines), None)
        return 0

    if args.command == "glyph-sheet":
        html_doc = render_glyph_sheet(args.script_id, boxes_per_row=args.boxes)
        _write_output(html_doc, args.output)
        return 0

    if args.command == "practice-sheet":
        html_doc = render_practice_sheet(args.ref, practice_rows=args.rows)
        _write_output(html_doc, args.output)
        return 0

    if args.command == "render-atlas":
        html_doc = render_atlas()
        _write_output(html_doc, args.output)
        return 0

    parser.error(f"unhandled command '{args.command}'")
    return 2
