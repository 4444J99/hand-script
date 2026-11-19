"""Tests for relationship-labeled lexical network and Unicode grapheme inspection."""

from __future__ import annotations

import copy
import json
from importlib import resources

import pytest

from hand_script.etymology import (
    EtymologyError,
    load_lexical_network,
    parse_lexical_network,
)
from hand_script.unicode_inspect import inspect_codepoint, inspect_text


def test_lexical_network_separates_cognates_from_translation_and_noga() -> None:
    net = load_lexical_network()
    assert len(net.clusters) == 5
    assert len(net.passages) == 8

    peace_edges = net.get_cluster_edges("peace-wholeness")
    rels = {(e.source, e.target): e.relation for e in peace_edges}
    assert rels[("sem-slm", "he-shalom")] == "cognate"
    assert rels[("sem-slm", "ar-salam")] == "cognate"
    assert rels[("he-shalom", "grc-eirene")] == "translation"
    assert rels[("he-shalom", "grc-soteria")] == "translation"

    foot_edges = net.get_cluster_edges("foot-step")
    foot_rels = {(e.source, e.target): e.relation for e in foot_edges}
    assert foot_rels[("pie-ped", "ru-peshij")] == "cognate"
    assert foot_rels[("ru-peshij", "ru-noga")] == "comparison"
    assert ("pie-ped", "ru-noga") not in foot_rels


def test_lexical_network_forbids_cross_family_cognate_edges() -> None:
    raw = json.loads(
        resources.files("hand_script.data")
        .joinpath("lexical_network.json")
        .read_text(encoding="utf-8")
    )
    bad = copy.deepcopy(raw)
    bad["edges"].append(
        {
            "cluster": "peace-wholeness",
            "source": "he-shalom",
            "target": "grc-eirene",
            "relation": "cognate",
            "evidence": "Invalid false cognate across Afroasiatic and Indo-European.",
        }
    )
    with pytest.raises(EtymologyError, match="cross-family 'cognate' edge forbidden"):
        parse_lexical_network(bad)


def test_lexical_network_forbids_cross_language_word_formation() -> None:
    raw = json.loads(
        resources.files("hand_script.data")
        .joinpath("lexical_network.json")
        .read_text(encoding="utf-8")
    )
    bad = copy.deepcopy(raw)
    bad["edges"].append(
        {
            "cluster": "write-script-book",
            "source": "he-katav",
            "target": "ar-kitab",
            "relation": "word_formation",
            "evidence": "Invalid cross-language word_formation.",
        }
    )
    with pytest.raises(EtymologyError, match="'word_formation' requires shared language"):
        parse_lexical_network(bad)


def test_unicode_inspector_decomposes_polytonic_niqqud_and_virama() -> None:
    # Greek polytonic circumflex on Μῆνιν
    grc = inspect_text("Μῆνιν")
    assert len(grc) == 5
    assert grc[1].base.codepoint == "U+03B7"
    assert any(m.codepoint == "U+0342" for m in grc[1].marks)

    # Hebrew shalom with shin dot + qamats
    heb = inspect_text("שָׁלוֹם")
    assert len(heb) == 4
    assert heb[0].base.name == "HEBREW LETTER SHIN"
    assert heb[0].base.bidirectional == "R"
    assert len(heb[0].marks) == 2
    assert heb[-1].base.name == "HEBREW LETTER FINAL MEM"

    # Devanagari pad- with virama
    dev = inspect_text("पद्")
    assert len(dev) == 2
    assert dev[1].marks[0].name == "DEVANAGARI SIGN VIRAMA"

    with pytest.raises(ValueError, match="single Unicode character"):
        inspect_codepoint("ab")
