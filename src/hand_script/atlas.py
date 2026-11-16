"""Deterministic self-contained HTML comparative atlas across all project registries."""

from __future__ import annotations

import html

from hand_script.curriculum import (
    LanguageMap,
    LinguisticsCanon,
    load_language_map,
    load_linguistics_canon,
)
from hand_script.etymology import LexicalNetwork, load_lexical_network
from hand_script.manifest import ProjectManifest, load_manifest
from hand_script.scripts import ScriptCatalog, load_script_catalog

_ATLAS_CSS = """\
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 24px;
  background: #f5f4ef;
  color: #191919;
  font-family: "Noto Serif", "Iowan Old Style", Georgia, serif;
  line-height: 1.5;
}
main {
  max-width: 1080px;
  margin: 0 auto;
  background: #ffffff;
  border: 1px solid #d5d1c8;
  padding: 28px 32px;
}
h1 { margin: 0 0 6px; font-size: 22pt; }
h2 {
  margin: 26px 0 10px;
  padding-bottom: 4px;
  border-bottom: 1.5px solid #2b2b2b;
  font-size: 14.5pt;
}
h3 { margin: 16px 0 6px; font-size: 11.5pt; }
p.lead { margin: 0 0 14px; color: #3a3a3a; font-size: 10.5pt; }
.audit-callout {
  background: #f8f6f0;
  border-left: 3px solid #4d4b44;
  padding: 10px 14px;
  margin: 12px 0;
  font-size: 9.5pt;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin: 10px 0 16px;
  font-size: 9.4pt;
}
th, td {
  border: 1px solid #dad6cd;
  padding: 6px 8px;
  text-align: left;
  vertical-align: top;
}
th { background: #f1efe9; font-weight: 700; }
.tag {
  display: inline-block;
  font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 8pt;
  background: #ece9e0;
  padding: 1px 6px;
  border-radius: 2px;
}
.track-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
  gap: 12px;
}
.card {
  border: 1px solid #dbd7ce;
  padding: 10px 12px;
  background: #fcfbf9;
}
@media print {
  body { background: #ffffff; padding: 0; }
  main { max-width: none; border: none; padding: 0; }
}
"""


def render_atlas(
    *,
    manifest: ProjectManifest | None = None,
    catalog: ScriptCatalog | None = None,
    languages: LanguageMap | None = None,
    network: LexicalNetwork | None = None,
    canon: LinguisticsCanon | None = None,
) -> str:
    """Render a deterministic, standalone HTML comparative atlas."""
    mf = manifest or load_manifest()
    cat = catalog or load_script_catalog()
    lang_map = languages or load_language_map(script_catalog=cat)
    net = network or load_lexical_network(script_catalog=cat)
    lin_canon = canon or load_linguistics_canon()

    counts = lang_map.count_audit()
    family_names = {f.id: f.name for f in lang_map.families}
    nodes_by_id = net.nodes_by_id()

    script_rows = []
    for sc in cat.scripts:
        dir_attr = "rtl" if sc.direction == "rtl" else "ltr"
        specimen = " · ".join(g.glyph for g in sc.exemplars[:4])
        script_rows.append(
            "<tr>"
            f"<td><strong>{html.escape(sc.name)}</strong></td>"
            f'<td><span class="tag">{html.escape(sc.typology)}</span></td>'
            f"<td>{html.escape(sc.encoded_unit)}</td>"
            f"<td>{html.escape(sc.direction)} / {html.escape(sc.ruling)}</td>"
            f"<td>{html.escape(sc.interference_group)}</td>"
            f'<td dir="{dir_attr}"><bdi>{html.escape(specimen)}</bdi></td>'
            "</tr>"
        )

    track_cards = []
    for tr in cat.tracks:
        seq = " &rarr; ".join(html.escape(s) for s in tr.scripts)
        track_cards.append(
            '<div class="card">'
            f"<h3>{html.escape(tr.id)} "
            f'(<span class="tag">{html.escape(tr.source)}</span>)</h3>'
            f"<p><strong>Order:</strong> {seq}</p>"
            f"<p>{html.escape(tr.description)}</p>"
            "</div>"
        )

    lang_rows = []
    for lg in lang_map.languages:
        pathway_summary = "; ".join(
            f"{html.escape(p.label)} ({', '.join(html.escape(t) for t in p.founding_texts)})"
            for p in lg.pathways
        )
        lang_rows.append(
            "<tr>"
            f"<td><strong>{html.escape(lg.name)}</strong></td>"
            f"<td>{html.escape(family_names[lg.family])}<br>"
            f"<small>{html.escape(lg.branch)}</small></td>"
            f"<td>Tier {lg.tier}</td>"
            f'<td><span class="tag">{html.escape(lg.archive_status)}</span></td>'
            f"<td>{html.escape(', '.join(lg.scripts))}</td>"
            f"<td>{pathway_summary}</td>"
            "</tr>"
        )

    cluster_blocks = []
    for cl in net.clusters:
        edge_rows = []
        for edge in net.get_cluster_edges(cl.id):
            src = nodes_by_id[edge.source]
            tgt = nodes_by_id[edge.target]
            passage_note = f" [{html.escape(edge.passage)}]" if edge.passage else ""
            edge_rows.append(
                "<tr>"
                f'<td><span class="tag">{html.escape(edge.relation)}</span></td>'
                f"<td><bdi>{html.escape(src.form)}</bdi> "
                f"({html.escape(src.language)})</td>"
                f"<td><bdi>{html.escape(tgt.form)}</bdi> "
                f"({html.escape(tgt.language)})</td>"
                f"<td>{html.escape(edge.evidence)}{passage_note}</td>"
                "</tr>"
            )
        cluster_blocks.append(
            f"<h3>{html.escape(cl.title)}</h3>"
            f"<p>{html.escape(cl.summary)}</p>"
            "<table><thead><tr>"
            "<th>Relation</th><th>Source</th><th>Target</th><th>Evidence</th>"
            f"</tr></thead><tbody>{''.join(edge_rows)}</tbody></table>"
        )

    canon_rows = []
    for wk in lin_canon.works:
        canon_rows.append(
            "<tr>"
            f'<td><span class="tag">{html.escape(wk.stage)}</span></td>'
            f"<td>{html.escape(wk.subfield)}</td>"
            f"<td>{html.escape(wk.authors)} ({wk.year})</td>"
            f"<td><strong>{html.escape(wk.title)}</strong></td>"
            f"<td>{html.escape(wk.focus)}</td>"
            "</tr>"
        )

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        "  <title>Hand-Script Comparative Atlas</title>\n"
        f"  <style>{_ATLAS_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        "<main>\n"
        "  <h1>hand-script — Writing Systems, Comparative Roots, and Practice Atlas</h1>\n"
        '  <p class="lead">'
        f"Space <code>{html.escape(mf.space.id)}</code> · "
        f"{len(cat.scripts)} writing systems · "
        f"{counts['turn6_core_languages']} Turn-6 core + "
        f"{counts['archive_expansion_languages']} expansion languages · "
        f"{len(net.clusters)} typed lexical clusters · "
        f"{len(lin_canon.works)} staged linguistics works."
        "</p>\n"
        '  <div class="audit-callout">\n'
        "    <strong>Repository Boundary &amp; Archive Audit:</strong> "
        "Middle English scansion and Canterbury Tales phonological modeling live in "
        "<code>4444J99/chaucer</code>; poetry studio artifacts live in "
        "<code>4444J99/versforms</code> and <code>4444J99/journal-handwritten-web</code>. "
        f"{html.escape(lang_map.source_note)}\n"
        "  </div>\n"
        "  <h2>1. Writing Systems &amp; Ruling Typology (Daniels &amp; Bright 1996)</h2>\n"
        f"  <p><strong>Authority:</strong> {html.escape(cat.typology_authority)}. "
        f"{html.escape(cat.sequencing_note)}</p>\n"
        "  <table><thead><tr>"
        "<th>Script</th><th>Daniels Type</th><th>Primary Unit</th>"
        "<th>Direction &amp; Ruling</th><th>Interference Group</th><th>Exemplars</th>"
        f"</tr></thead><tbody>{''.join(script_rows)}</tbody></table>\n"
        "  <h2>2. Sequencing Hypotheses &amp; Interference Control</h2>\n"
        f'  <div class="track-grid">{"".join(track_cards)}</div>\n'
        "  <h2>3. Comparative Languages &amp; Founding Text Pathways</h2>\n"
        "  <table><thead><tr>"
        "<th>Language</th><th>Family &amp; Branch</th><th>Tier</th>"
        "<th>Archive Status</th><th>Scripts</th><th>Historical Pathways &amp; Texts</th>"
        f"</tr></thead><tbody>{''.join(lang_rows)}</tbody></table>\n"
        "  <h2>4. Relationship-Labeled Lexical &amp; Translation Network</h2>\n"
        f"  <p>{html.escape(net.design_rule)}</p>\n"
        f"  {''.join(cluster_blocks)}\n"
        "  <h2>5. Staged Linguistics Meta-Canon</h2>\n"
        f"  <p>{html.escape(lin_canon.caveat)}</p>\n"
        "  <table><thead><tr>"
        "<th>Stage</th><th>Subfield</th><th>Author (Year)</th>"
        "<th>Work</th><th>Core Contribution</th>"
        f"</tr></thead><tbody>{''.join(canon_rows)}</tbody></table>\n"
        "</main>\n"
        "</body>\n"
        "</html>\n"
    )
