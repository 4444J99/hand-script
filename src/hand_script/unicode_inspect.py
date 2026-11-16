"""Pure-stdlib Unicode codepoint and grapheme-cluster inspector for script learners."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class CodepointInfo:
    char: str
    codepoint: str
    name: str
    category: str
    combining_class: int
    bidirectional: str
    east_asian_width: str
    is_combining: bool


@dataclass(frozen=True)
class GraphemeBreakdown:
    surface: str
    base: CodepointInfo
    marks: tuple[CodepointInfo, ...]


def inspect_codepoint(ch: str) -> CodepointInfo:
    if len(ch) != 1:
        raise ValueError(f"expected single Unicode character, got length {len(ch)}")
    cp = ord(ch)
    cat = unicodedata.category(ch)
    comb = unicodedata.combining(ch)
    return CodepointInfo(
        char=ch,
        codepoint=f"U+{cp:04X}",
        name=unicodedata.name(ch, "<UNNAMED>"),
        category=cat,
        combining_class=comb,
        bidirectional=unicodedata.bidirectional(ch),
        east_asian_width=unicodedata.east_asian_width(ch),
        is_combining=cat.startswith("M") or comb > 0,
    )


def inspect_text(
    text: str, *, normalize: str | None = "NFC", skip_whitespace: bool = False
) -> tuple[GraphemeBreakdown, ...]:
    """Segment `text` into base characters plus attached combining marks.

    Decomposes a normalized copy (`NFD`) when a precomposed character hides
    diacritics (such as polytonic Greek `ῆ` -> `η` + circumflex), while keeping
    visible surface clusters together for Hebrew niqqud, Arabic harakat, and
    Devanagari matras/virama.
    """
    working = unicodedata.normalize(normalize, text) if normalize else text
    nfd = unicodedata.normalize("NFD", working)

    clusters: list[list[str]] = []
    for ch in nfd:
        if skip_whitespace and ch.isspace():
            continue
        info = inspect_codepoint(ch)
        if info.is_combining and clusters:
            clusters[-1].append(ch)
        else:
            clusters.append([ch])

    results: list[GraphemeBreakdown] = []
    for raw_cluster in clusters:
        base_info = inspect_codepoint(raw_cluster[0])
        mark_infos = tuple(inspect_codepoint(m) for m in raw_cluster[1:])
        surface = unicodedata.normalize("NFC", "".join(raw_cluster))
        results.append(GraphemeBreakdown(surface=surface, base=base_info, marks=mark_infos))
    return tuple(results)
