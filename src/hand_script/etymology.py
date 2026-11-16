"""Relationship-labeled lexical & textual network (`hand-script.lexical-network/1`)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from hand_script.scripts import ScriptCatalog, load_script_catalog

EXPECTED_SCHEMA = "hand-script.lexical-network/1"
VALID_NODE_KINDS = frozenset({"root", "lexeme"})
VALID_RELATIONS = frozenset(
    {
        "cognate",
        "word_formation",
        "borrowing",
        "translation",
        "interpretation",
        "comparison",
    }
)


class EtymologyError(ValueError):
    """Raised when `lexical_network.json` violates structural or historical invariants."""


@dataclass(frozen=True)
class LexicalNode:
    id: str
    kind: str
    family: str
    language: str
    script: str
    form: str
    transliteration: str
    gloss: str


@dataclass(frozen=True)
class ConceptCluster:
    id: str
    title: str
    summary: str


@dataclass(frozen=True)
class LexicalEdge:
    cluster: str
    source: str
    target: str
    relation: str
    evidence: str
    passage: str | None = None


@dataclass(frozen=True)
class PracticePassage:
    ref: str
    work: str
    language: str
    script: str
    text: str
    transliteration: str
    gloss: str
    focus_nodes: tuple[str, ...]
    practice_note: str


@dataclass(frozen=True)
class LexicalNetwork:
    schema: str
    design_rule: str
    nodes: tuple[LexicalNode, ...]
    clusters: tuple[ConceptCluster, ...]
    edges: tuple[LexicalEdge, ...]
    passages: tuple[PracticePassage, ...]

    def nodes_by_id(self) -> dict[str, LexicalNode]:
        return {node.id: node for node in self.nodes}

    def clusters_by_id(self) -> dict[str, ConceptCluster]:
        return {cluster.id: cluster for cluster in self.clusters}

    def get_cluster_edges(
        self, cluster_id: str, *, relation: str | None = None
    ) -> tuple[LexicalEdge, ...]:
        if cluster_id not in self.clusters_by_id():
            known = ", ".join(sorted(self.clusters_by_id()))
            raise KeyError(f"unknown cluster '{cluster_id}' (known: {known})")
        if relation is not None and relation not in VALID_RELATIONS:
            raise EtymologyError(f"invalid relation filter '{relation}'")
        return tuple(
            edge
            for edge in self.edges
            if edge.cluster == cluster_id and (relation is None or edge.relation == relation)
        )

    def edges_for_node_ids(self, node_ids: tuple[str, ...]) -> tuple[LexicalEdge, ...]:
        focus = set(node_ids)
        if not focus:
            return ()
        return tuple(edge for edge in self.edges if edge.source in focus or edge.target in focus)

    def get_passage(self, ref: str) -> PracticePassage:
        for passage in self.passages:
            if passage.ref == ref:
                return passage
        known = ", ".join(p.ref for p in self.passages)
        raise KeyError(f"unknown passage ref '{ref}' (known: {known})")


def _require_str(mapping: dict[str, Any], key: str, ctx: str) -> str:
    val = mapping.get(key)
    if not isinstance(val, str) or not val.strip():
        raise EtymologyError(f"{ctx}: missing or empty string '{key}'")
    return val


def parse_lexical_network(
    raw: dict[str, Any], script_catalog: ScriptCatalog | None = None
) -> LexicalNetwork:
    if not isinstance(raw, dict):
        raise EtymologyError("lexical network root must be a JSON object")
    schema = _require_str(raw, "schema", "network")
    if schema != EXPECTED_SCHEMA:
        raise EtymologyError(
            f"network: unsupported schema '{schema}' (expected '{EXPECTED_SCHEMA}')"
        )
    design_rule = _require_str(raw, "design_rule", "network")

    catalog = script_catalog or load_script_catalog()
    valid_scripts = set(catalog.by_id())

    nodes_raw = raw.get("nodes")
    if not isinstance(nodes_raw, list) or not nodes_raw:
        raise EtymologyError("network.nodes must be a non-empty list")

    nodes_by_id: dict[str, LexicalNode] = {}
    nodes: list[LexicalNode] = []
    for idx, entry in enumerate(nodes_raw):
        ctx = f"nodes[{idx}]"
        if not isinstance(entry, dict):
            raise EtymologyError(f"{ctx} must be an object")
        nid = _require_str(entry, "id", ctx)
        if nid in nodes_by_id:
            raise EtymologyError(f"{ctx}: duplicate node id '{nid}'")
        kind = _require_str(entry, "kind", ctx)
        if kind not in VALID_NODE_KINDS:
            raise EtymologyError(f"{ctx}: invalid node kind '{kind}'")
        script = _require_str(entry, "script", ctx)
        if script not in valid_scripts:
            raise EtymologyError(f"{ctx}: unknown script '{script}'")
        node = LexicalNode(
            id=nid,
            kind=kind,
            family=_require_str(entry, "family", ctx),
            language=_require_str(entry, "language", ctx),
            script=script,
            form=_require_str(entry, "form", ctx),
            transliteration=_require_str(entry, "transliteration", ctx),
            gloss=_require_str(entry, "gloss", ctx),
        )
        nodes_by_id[nid] = node
        nodes.append(node)

    clusters_raw = raw.get("clusters")
    if not isinstance(clusters_raw, list) or not clusters_raw:
        raise EtymologyError("network.clusters must be a non-empty list")
    seen_clusters: set[str] = set()
    clusters: list[ConceptCluster] = []
    for idx, entry in enumerate(clusters_raw):
        ctx = f"clusters[{idx}]"
        if not isinstance(entry, dict):
            raise EtymologyError(f"{ctx} must be an object")
        cid = _require_str(entry, "id", ctx)
        if cid in seen_clusters:
            raise EtymologyError(f"{ctx}: duplicate cluster id '{cid}'")
        seen_clusters.add(cid)
        clusters.append(
            ConceptCluster(
                id=cid,
                title=_require_str(entry, "title", ctx),
                summary=_require_str(entry, "summary", ctx),
            )
        )

    edges_raw = raw.get("edges")
    if not isinstance(edges_raw, list) or not edges_raw:
        raise EtymologyError("network.edges must be a non-empty list")
    edges: list[LexicalEdge] = []
    for idx, entry in enumerate(edges_raw):
        ctx = f"edges[{idx}]"
        if not isinstance(entry, dict):
            raise EtymologyError(f"{ctx} must be an object")
        cluster = _require_str(entry, "cluster", ctx)
        if cluster not in seen_clusters:
            raise EtymologyError(f"{ctx}: unknown cluster '{cluster}'")
        src_id = _require_str(entry, "source", ctx)
        tgt_id = _require_str(entry, "target", ctx)
        if src_id not in nodes_by_id:
            raise EtymologyError(f"{ctx}: unknown source node '{src_id}'")
        if tgt_id not in nodes_by_id:
            raise EtymologyError(f"{ctx}: unknown target node '{tgt_id}'")
        if src_id == tgt_id:
            raise EtymologyError(f"{ctx}: self-loop edge on '{src_id}'")
        relation = _require_str(entry, "relation", ctx)
        if relation not in VALID_RELATIONS:
            raise EtymologyError(f"{ctx}: invalid relation '{relation}'")

        src_node = nodes_by_id[src_id]
        tgt_node = nodes_by_id[tgt_id]
        if relation == "cognate" and src_node.family != tgt_node.family:
            raise EtymologyError(
                f"{ctx}: cross-family 'cognate' edge forbidden between "
                f"{src_id} ({src_node.family}) and {tgt_id} ({tgt_node.family}); "
                "use translation, borrowing, interpretation, or comparison."
            )
        if relation == "word_formation" and src_node.language != tgt_node.language:
            raise EtymologyError(
                f"{ctx}: 'word_formation' requires shared language, got "
                f"{src_node.language} -> {tgt_node.language}"
            )

        passage_val = entry.get("passage")
        if passage_val is not None and (
            not isinstance(passage_val, str) or not passage_val.strip()
        ):
            raise EtymologyError(f"{ctx}: passage must be a non-empty string if present")

        edges.append(
            LexicalEdge(
                cluster=cluster,
                source=src_id,
                target=tgt_id,
                relation=relation,
                evidence=_require_str(entry, "evidence", ctx),
                passage=passage_val,
            )
        )

    passages_raw = raw.get("passages")
    if not isinstance(passages_raw, list) or not passages_raw:
        raise EtymologyError("network.passages must be a non-empty list")
    seen_refs: set[str] = set()
    passages: list[PracticePassage] = []
    for idx, entry in enumerate(passages_raw):
        ctx = f"passages[{idx}]"
        if not isinstance(entry, dict):
            raise EtymologyError(f"{ctx} must be an object")
        ref = _require_str(entry, "ref", ctx)
        if ref in seen_refs:
            raise EtymologyError(f"{ctx}: duplicate passage ref '{ref}'")
        seen_refs.add(ref)
        script = _require_str(entry, "script", ctx)
        if script not in valid_scripts:
            raise EtymologyError(f"{ctx}: unknown script '{script}'")
        focus_raw = entry.get("focus_nodes", [])
        if not isinstance(focus_raw, list):
            raise EtymologyError(f"{ctx}: focus_nodes must be a list")
        focus_nodes: list[str] = []
        for fn in focus_raw:
            if not isinstance(fn, str) or fn not in nodes_by_id:
                raise EtymologyError(f"{ctx}: unknown focus node '{fn}'")
            focus_nodes.append(fn)

        passages.append(
            PracticePassage(
                ref=ref,
                work=_require_str(entry, "work", ctx),
                language=_require_str(entry, "language", ctx),
                script=script,
                text=_require_str(entry, "text", ctx),
                transliteration=_require_str(entry, "transliteration", ctx),
                gloss=_require_str(entry, "gloss", ctx),
                focus_nodes=tuple(focus_nodes),
                practice_note=_require_str(entry, "practice_note", ctx),
            )
        )

    return LexicalNetwork(
        schema=schema,
        design_rule=design_rule,
        nodes=tuple(nodes),
        clusters=tuple(clusters),
        edges=tuple(edges),
        passages=tuple(passages),
    )


def load_lexical_network(
    path: Path | None = None, script_catalog: ScriptCatalog | None = None
) -> LexicalNetwork:
    if path is None:
        raw_text = (
            resources.files("hand_script.data")
            .joinpath("lexical_network.json")
            .read_text(encoding="utf-8")
        )
    else:
        raw_text = path.read_text(encoding="utf-8")
    return parse_lexical_network(json.loads(raw_text), script_catalog=script_catalog)
