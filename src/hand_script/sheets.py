"""Printable HTML practice sheets: letter sheets and line-copy sheets."""

from __future__ import annotations

from html import escape

CSS = """
@page { size: A4; margin: 12mm; }
* { box-sizing: border-box; }
body { font-family: Helvetica, Arial, sans-serif; color: #222; margin: 0; }
h1 { font-size: 16pt; margin: 0 0 2mm; }
.sub { font-size: 9pt; color: #666; margin-bottom: 4mm; }
.row { display: flex; align-items: center; border-bottom: 0.2mm solid #ddd;
       page-break-inside: avoid; }
.meta { width: 26mm; font-size: 8pt; line-height: 1.2; flex: none; }
.meta b { font-size: 10pt; }
.cells { display: flex; flex: 1; }
.cells.rtl { flex-direction: row-reverse; }
.cell { position: relative; width: 14mm; height: 14mm; flex: none;
        border-left: 0.2mm solid #ccc; text-align: center;
        font-size: 30pt; line-height: 14mm; }
.cell i { position: absolute; left: 0; right: 0; height: 0;
          border-top: 0.2mm solid #9bd; }
.cell i.base { border-top: 0.35mm solid #47a; top: 10.5mm; }
.cell i.mid { top: 6mm; border-top-style: dashed; }
.cell i.top { top: 2mm; }
.cell span { position: relative; color: #bbb; z-index: 1; }
.cell.model span { color: #555; }
.cell.blank span { color: transparent; }
.copy { margin-bottom: 3mm; page-break-inside: avoid; }
.copy .src { font-size: 8pt; color: #666; }
.copy .gloss { font-size: 8pt; color: #888; font-style: italic; }
.line { position: relative; height: 16mm; border-bottom: 0.35mm solid #47a; }
.line::before { content: ""; position: absolute; left: 0; right: 0; top: 6mm;
                border-top: 0.2mm dashed #9bd; }
.line.model { font-size: 26pt; line-height: 16mm; color: #bbb; white-space: nowrap; overflow: hidden; }
.line.model.dark { color: #555; }
"""

GUIDES = '<i class="top"></i><i class="mid"></i><i class="base"></i>'


def _page(title: str, body: str, direction: str, font: str) -> str:
    return (
        "<!doctype html>\n"
        f'<html lang="en"><head><meta charset="utf-8"><title>{escape(title)}</title>'
        f"<style>{CSS}\n.cell, .line.model {{ font-family: {font}; }}</style></head>"
        f'<body dir="ltr">{body}</body></html>\n'
    )


def _cell(char: str, kind: str) -> str:
    return f'<div class="cell {kind}">{GUIDES}<span>{escape(char)}</span></div>'


def letter_sheet(script: dict, ghosts: int = 2, blanks: int = 8) -> str:
    """One row per letter form: a dark model, `ghosts` light copies, then blanks."""
    rtl = script["direction"] == "rtl"
    rows = []
    for letter in script["letters"]:
        for form in letter["practice"]:
            cells = [_cell(form, "model")]
            cells += [_cell(form, "ghost") for _ in range(ghosts)]
            cells += [_cell(form, "blank") for _ in range(blanks)]
            meta = f'<b>{escape(letter["name"])}</b><br>{escape(letter["sound"])}'
            rows.append(
                f'<div class="row"><div class="meta">{meta}</div>'
                f'<div class="cells{" rtl" if rtl else ""}">{"".join(cells)}</div></div>'
            )
    head = (
        f'<h1>{escape(script["name"])} letters</h1>'
        f'<div class="sub">{escape(script["reason"])} &middot; trace the model, '
        "copy the light letters, then write from memory in the blank cells.</div>"
    )
    return _page(f'{script["name"]} letter sheet', head + "".join(rows), script["direction"], script["font"])


def copy_sheet(script: dict, blank_lines: int = 2) -> str:
    """Model line to copy, a ghost trace line, then blank ruled lines per text."""
    rtl = script["direction"] == "rtl"
    style = ' style="direction:rtl;text-align:right"' if rtl else ""
    blocks = []
    for item in script["copy_lines"]:
        text = escape(item["text"])
        blocks.append(
            '<div class="copy">'
            f'<div class="src">{escape(item["source"])}</div>'
            f'<div class="line model dark"{style}>{text}</div>'
            f'<div class="line model"{style}>{text}</div>'
            + '<div class="line"></div>' * blank_lines
            + f'<div class="gloss">{escape(item["gloss"])}</div></div>'
        )
    head = (
        f'<h1>{escape(script["name"])} line copying</h1>'
        '<div class="sub">Daily minimum: copy 3-5 lines by hand, slowly. '
        "Script first, grammar second, translation third.</div>"
    )
    return _page(f'{script["name"]} copy sheet', head + "".join(blocks), script["direction"], script["font"])
