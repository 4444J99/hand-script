"""Deterministic printable A4 HTML handwriting sheets across four ruling geometries."""

from __future__ import annotations

import html

from hand_script.etymology import (
    LexicalNetwork,
    PracticePassage,
    load_lexical_network,
)
from hand_script.notebook import PROTOCOL_STEPS
from hand_script.scripts import ScriptCatalog, ScriptSpec, load_script_catalog
from hand_script.unicode_inspect import inspect_text

_SHEET_CSS = """\
@page { size: A4 portrait; margin: 12mm; }
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 16px 20px;
  background: #f6f5f1;
  color: #181818;
  font-family: "Noto Serif", "Iowan Old Style", "Palatino Linotype", Georgia, serif;
  font-size: 10.5pt;
  line-height: 1.42;
}
main {
  max-width: 190mm;
  margin: 0 auto;
  background: #ffffff;
  border: 1px solid #d4d0c8;
  padding: 16px 20px 20px;
}
header.sheet-header {
  border-bottom: 1.5px solid #222222;
  padding-bottom: 8px;
  margin-bottom: 12px;
}
header.sheet-header h1 {
  margin: 0 0 4px;
  font-size: 15pt;
  font-weight: 700;
  letter-spacing: 0.01em;
}
.meta-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 14px;
  font-size: 8.8pt;
  color: #3d3d3d;
}
.caveat-box {
  background: #f8f7f3;
  border-left: 3px solid #5a5a52;
  padding: 6px 10px;
  margin: 8px 0 12px;
  font-size: 8.6pt;
  color: #333333;
}
.principles {
  margin: 0 0 12px;
  padding-left: 18px;
  font-size: 9pt;
}
.principles li { margin-bottom: 2px; }
section.glyph-card, section.passage-card {
  border: 1px solid #dbd7cf;
  padding: 8px 10px;
  margin-bottom: 10px;
  break-inside: avoid;
}
.glyph-header, .passage-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 4px;
}
.glyph-specimen {
  font-size: 16pt;
  font-weight: 600;
  padding-right: 6px;
}
.codepoints, .badge {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 8pt;
  color: #444444;
  background: #f0eee8;
  padding: 1px 5px;
  border-radius: 2px;
}
.subnote {
  font-size: 8.6pt;
  color: #424242;
  margin: 2px 0 6px;
}
.passage-specimen {
  font-size: 13.5pt;
  margin: 4px 0;
  padding: 4px 6px;
  background: #faf9f6;
  border: 1px solid #ece9e1;
}
.lexical-list {
  margin: 4px 0 6px;
  padding-left: 16px;
  font-size: 8.4pt;
  color: #2f2f2f;
}
.ruling-wrap {
  margin: 4px 0;
}
svg.ruling {
  width: 100%;
  height: auto;
  display: block;
}
.protocol-footer {
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid #c8c4bc;
  font-size: 8.4pt;
  color: #363636;
  break-inside: avoid;
}
.protocol-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px 10px;
  margin-top: 4px;
}
@media print {
  body { background: #ffffff; padding: 0; }
  main { max-width: none; border: none; padding: 0; }
}
"""


def _dir_attr(script: ScriptSpec) -> str:
    return "rtl" if script.direction == "rtl" else "ltr"


def render_ruling_svg(
    ruling: str,
    *,
    trace_text: str = "",
    boxes_per_row: int = 10,
    label: str = "",
) -> str:
    """Render a deterministic inline SVG ruling row for handwriting practice."""
    escaped_trace = html.escape(trace_text)
    escaped_label = html.escape(label)

    if ruling == "square-grid":
        box_size = 56
        gap = 6
        total_w = boxes_per_row * box_size + (boxes_per_row - 1) * gap
        total_h = box_size + (14 if escaped_label else 2)
        y0 = 12 if escaped_label else 1
        trace_chars = [ch for ch in trace_text if not ch.isspace() and ch not in "()/·,"]
        parts = [
            f'<svg class="ruling ruling-square-grid" '
            f'viewBox="0 0 {total_w} {total_h}" '
            f'xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-label="square-grid handwriting ruling">'
        ]
        if escaped_label:
            parts.append(f'<text x="0" y="9" font-size="8" fill="#666666">{escaped_label}</text>')
        for idx in range(boxes_per_row):
            x = idx * (box_size + gap)
            mid_x = x + box_size / 2
            mid_y = y0 + box_size / 2
            parts.append(
                f'<rect x="{x}" y="{y0}" width="{box_size}" height="{box_size}" '
                f'fill="none" stroke="#8a867e" stroke-width="1"/>'
            )
            parts.append(
                f'<line x1="{mid_x}" y1="{y0}" x2="{mid_x}" y2="{y0 + box_size}" '
                f'stroke="#c8c4bc" stroke-width="0.7" stroke-dasharray="3,3"/>'
            )
            parts.append(
                f'<line x1="{x}" y1="{mid_y}" x2="{x + box_size}" y2="{mid_y}" '
                f'stroke="#c8c4bc" stroke-width="0.7" stroke-dasharray="3,3"/>'
            )
            if idx < len(trace_chars):
                ch_esc = html.escape(trace_chars[idx])
                parts.append(
                    f'<text x="{mid_x}" y="{y0 + box_size * 0.72:.1f}" '
                    f'text-anchor="middle" font-size="32" fill="#cac6be">{ch_esc}</text>'
                )
        parts.append("</svg>")
        return "".join(parts)

    width = 680
    height = 56
    parts = [
        f'<svg class="ruling ruling-{html.escape(ruling)}" '
        f'viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="{html.escape(ruling)} handwriting ruling">'
    ]
    if escaped_label:
        parts.append(f'<text x="2" y="9" font-size="8" fill="#666666">{escaped_label}</text>')

    if ruling == "four-line":
        # Ascender (14), x-height dashed (25), solid baseline (40), descender (51)
        parts.append(
            f'<line x1="0" y1="14" x2="{width}" y2="14" stroke="#bfb9ae" stroke-width="0.8"/>'
        )
        parts.append(
            f'<line x1="0" y1="25" x2="{width}" y2="25" '
            f'stroke="#aba59a" stroke-width="0.8" stroke-dasharray="4,4"/>'
        )
        parts.append(
            f'<line x1="0" y1="40" x2="{width}" y2="40" stroke="#4a4741" stroke-width="1.1"/>'
        )
        parts.append(
            f'<line x1="0" y1="51" x2="{width}" y2="51" stroke="#d0cbc1" stroke-width="0.8"/>'
        )
        if escaped_trace:
            parts.append(f'<text x="8" y="39" font-size="21" fill="#c8c4bc">{escaped_trace}</text>')

    elif ruling == "abjad-rtl":
        # Upper mark zone (14), mid guide (24), baseline (39), tail/descender (51), RTL cue on right
        parts.append(
            f'<line x1="0" y1="14" x2="{width}" y2="14" '
            f'stroke="#cbc5ba" stroke-width="0.7" stroke-dasharray="3,4"/>'
        )
        parts.append(
            f'<line x1="0" y1="24" x2="{width}" y2="24" '
            f'stroke="#b5afa4" stroke-width="0.8" stroke-dasharray="4,4"/>'
        )
        parts.append(
            f'<line x1="0" y1="39" x2="{width}" y2="39" stroke="#4a4741" stroke-width="1.15"/>'
        )
        parts.append(
            f'<line x1="0" y1="51" x2="{width}" y2="51" stroke="#d0cbc1" stroke-width="0.8"/>'
        )
        parts.append(
            f'<text x="{width - 4}" y="10" text-anchor="end" '
            f'font-size="8" fill="#555555">RTL &#9665;</text>'
        )
        if escaped_trace:
            parts.append(
                f'<text x="{width - 14}" y="38" text-anchor="end" direction="rtl" '
                f'font-size="22" fill="#c8c4bc">{escaped_trace}</text>'
            )

    elif ruling == "head-line":
        # Upper matra zone (11), heavy Shirorekha head-line (20), base (40), sub-base matra (51)
        parts.append(
            f'<line x1="0" y1="11" x2="{width}" y2="11" '
            f'stroke="#cdc7bc" stroke-width="0.7" stroke-dasharray="3,4"/>'
        )
        parts.append(
            f'<line x1="0" y1="20" x2="{width}" y2="20" stroke="#3f3c37" stroke-width="1.35"/>'
        )
        parts.append(
            f'<line x1="0" y1="40" x2="{width}" y2="40" '
            f'stroke="#a8a297" stroke-width="0.85" stroke-dasharray="4,3"/>'
        )
        parts.append(
            f'<line x1="0" y1="51" x2="{width}" y2="51" stroke="#d0cbc1" stroke-width="0.8"/>'
        )
        if escaped_trace:
            parts.append(f'<text x="8" y="39" font-size="21" fill="#c8c4bc">{escaped_trace}</text>')
    else:
        raise ValueError(f"unsupported ruling geometry '{ruling}'")

    parts.append("</svg>")
    return "".join(parts)


def _render_protocol_footer() -> str:
    cells = []
    for idx, (step_id, desc, weight) in enumerate(PROTOCOL_STEPS, start=1):
        pct = round(weight * 100)
        label = step_id.replace("_", " ")
        cells.append(
            f"<div><strong>{idx}. {html.escape(label)} ({pct}%):</strong> {html.escape(desc)}</div>"
        )
    return (
        '<footer class="protocol-footer">'
        "<strong>Six-Step Notebook Session Protocol (15-20 min baseline):</strong>"
        f'<div class="protocol-grid">{"".join(cells)}</div>'
        "</footer>"
    )


def _format_glyph_codepoints(glyph_text: str) -> str:
    cleaned = "".join(ch for ch in glyph_text if ch not in "()/·,")
    clusters = inspect_text(cleaned, skip_whitespace=True)
    codes: list[str] = []
    for cl in clusters:
        codes.append(cl.base.codepoint)
        for mark in cl.marks:
            codes.append(mark.codepoint)
    return " ".join(codes)


def render_glyph_sheet(
    script_id: str,
    *,
    catalog: ScriptCatalog | None = None,
    boxes_per_row: int = 10,
) -> str:
    """Render a deterministic A4 HTML exemplar glyph & stroke-principle sheet."""
    cat = catalog or load_script_catalog()
    spec = cat.get_script(script_id)
    text_dir = _dir_attr(spec)

    cards: list[str] = []
    for glyph in spec.exemplars:
        cp_label = _format_glyph_codepoints(glyph.glyph)
        if spec.ruling == "square-grid":
            trace_seed = glyph.glyph * 2
        else:
            spacer = "   "
            trace_seed = spacer.join([glyph.glyph] * 3)
        svg_row = render_ruling_svg(
            spec.ruling,
            trace_text=trace_seed,
            boxes_per_row=boxes_per_row,
            label="Trace & repeat from memory ->",
        )
        cards.append(
            '<section class="glyph-card">'
            '<div class="glyph-header">'
            f'<div><span class="glyph-specimen" dir="{text_dir}">'
            f"<bdi>{html.escape(glyph.glyph)}</bdi></span> "
            f"<strong>{html.escape(glyph.name)}</strong> "
            f"({html.escape(glyph.value)})</div>"
            f'<span class="codepoints">{html.escape(cp_label)}</span>'
            "</div>"
            f'<div class="subnote">{html.escape(glyph.form_note)}</div>'
            f'<div class="ruling-wrap">{svg_row}</div>'
            "</section>"
        )

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        f"  <title>Hand-Script Glyph Sheet — {html.escape(spec.name)}</title>\n"
        f"  <style>{_SHEET_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        "<main>\n"
        '  <header class="sheet-header">\n'
        f"    <h1>{html.escape(spec.name)} — Exemplar Glyph Sheet</h1>\n"
        '    <div class="meta-strip">\n'
        f"      <span><strong>Typology:</strong> {html.escape(spec.typology)}</span>\n"
        f"      <span><strong>Encoded Unit:</strong> "
        f"{html.escape(spec.encoded_unit)}</span>\n"
        f"      <span><strong>Direction:</strong> {html.escape(spec.direction)}</span>\n"
        f"      <span><strong>Ruling:</strong> {html.escape(spec.ruling)}</span>\n"
        f"      <span><strong>Interference Group:</strong> "
        f"{html.escape(spec.interference_group)}</span>\n"
        "    </div>\n"
        "  </header>\n"
        '  <div class="caveat-box">\n'
        "    <strong>Methodological Note:</strong> Faint trace glyphs come from standard "
        "typographic fonts to indicate structural proportion and component placement, not "
        "a calligraphic master exemplar. Handwriting practice builds grapheme-motor recall "
        "and orthographic awareness; track reading comprehension separately.\n"
        "  </div>\n"
        f'  <div class="subnote"><strong>Inventory:</strong> '
        f"{html.escape(spec.inventory_summary)}<br>"
        f"<strong>Ductus &amp; Proportion:</strong> "
        f"{html.escape(spec.ductus_notes)}</div>\n"
        f"  {''.join(cards)}\n"
        f"  {_render_protocol_footer()}\n"
        "</main>\n"
        "</body>\n"
        "</html>\n"
    )


def _render_passage_card(
    passage: PracticePassage,
    spec: ScriptSpec,
    network: LexicalNetwork,
    *,
    practice_rows: int,
) -> str:
    text_dir = _dir_attr(spec)
    nodes_lookup = network.nodes_by_id()
    related_edges = network.edges_for_node_ids(passage.focus_nodes)

    lex_items: list[str] = []
    for edge in related_edges[:4]:
        src = nodes_lookup[edge.source]
        tgt = nodes_lookup[edge.target]
        lex_items.append(
            f'<li><span class="badge">{html.escape(edge.relation)}</span> '
            f"<bdi>{html.escape(src.form)}</bdi> ({html.escape(src.language)}) "
            f"&rarr; <bdi>{html.escape(tgt.form)}</bdi> ({html.escape(tgt.language)}): "
            f"{html.escape(edge.evidence)}</li>"
        )
    lex_block = f'<ul class="lexical-list">{"".join(lex_items)}</ul>' if lex_items else ""

    rows_html: list[str] = []
    for row_idx in range(practice_rows):
        if row_idx == 0:
            trace = passage.text
            row_label = "Step 2 — Guided Copying (trace / copy attentively)"
        else:
            trace = ""
            row_label = "Step 3 — Memory Rewrite (cover specimen above and write from recall)"
        rows_html.append(
            '<div class="ruling-wrap">'
            + render_ruling_svg(
                spec.ruling,
                trace_text=trace,
                boxes_per_row=12,
                label=row_label,
            )
            + "</div>"
        )

    obs_row = (
        '<div class="ruling-wrap">'
        + render_ruling_svg(
            "four-line",
            trace_text="",
            label="Steps 4 & 6 — Structural Observation & Reflection Note",
        )
        + "</div>"
    )

    return (
        '<section class="passage-card">'
        '<div class="passage-header">'
        f"<div><strong>{html.escape(passage.work)}</strong> "
        f"({html.escape(spec.name)} · {html.escape(spec.typology)})</div>"
        f'<span class="badge">{html.escape(passage.ref)}</span>'
        "</div>"
        f'<div class="passage-specimen" dir="{text_dir}">'
        f"<bdi>{html.escape(passage.text)}</bdi></div>"
        f'<div class="subnote"><strong>Transliteration:</strong> '
        f"{html.escape(passage.transliteration)}<br>"
        f"<strong>Gloss:</strong> {html.escape(passage.gloss)}<br>"
        f"<strong>Handwriting Focus:</strong> {html.escape(passage.practice_note)}</div>"
        f"{lex_block}"
        f"{''.join(rows_html)}"
        f"{obs_row}"
        "</section>"
    )


def render_practice_sheet(
    passage_refs: list[str] | tuple[str, ...] | None = None,
    *,
    network: LexicalNetwork | None = None,
    catalog: ScriptCatalog | None = None,
    practice_rows: int = 2,
) -> str:
    """Render a deterministic A4 HTML multi-script opening-passage practice sheet."""
    if practice_rows < 1 or practice_rows > 5:
        raise ValueError("practice_rows must be between 1 and 5")
    cat = catalog or load_script_catalog()
    net = network or load_lexical_network(script_catalog=cat)

    if passage_refs is None:
        selected = net.passages
    else:
        selected = tuple(net.get_passage(ref) for ref in passage_refs)
    if not selected:
        raise ValueError("at least one passage is required to render a practice sheet")

    cards = [
        _render_passage_card(p, cat.get_script(p.script), net, practice_rows=practice_rows)
        for p in selected
    ]

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        "  <title>Hand-Script Canonical Passage Practice Sheet</title>\n"
        f"  <style>{_SHEET_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        "<main>\n"
        '  <header class="sheet-header">\n'
        "    <h1>Canonical Opening Passages — Multi-Script Handwriting Sheet</h1>\n"
        '    <div class="meta-strip">\n'
        f"      <span><strong>Passages:</strong> {len(selected)}</span>\n"
        "      <span><strong>Relation Discipline:</strong> "
        "cognate != translation != borrowing != comparison</span>\n"
        "    </div>\n"
        "  </header>\n"
        '  <div class="caveat-box">\n'
        "    <strong>Methodological Note:</strong> Each passage pairs script-appropriate "
        "ruling geometry (four-line, right-to-left abjad, Shirorekha head-line, or "
        "Tianzige square grid) with typed lexical links so inherited cognates are never "
        "conflated with Septuagint/Vulgate translation choices or script borrowings.\n"
        "  </div>\n"
        f"  {''.join(cards)}\n"
        f"  {_render_protocol_footer()}\n"
        "</main>\n"
        "</body>\n"
        "</html>\n"
    )
