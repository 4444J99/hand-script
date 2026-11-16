"""Project manifest loader and integrity checker (`hand-script.manifest/1`)."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

EXPECTED_SCHEMA = "hand-script.manifest/1"
VALID_COMPONENT_STATUSES = frozenset({"implemented", "not started", "planned"})
VALID_SCOPE_RELEVANCE = frozenset({"core", "supporting", "adjacent", "off-topic"})

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ManifestError(ValueError):
    """Raised when `project_manifest.json` violates structural or digest invariants."""


@dataclass(frozen=True)
class SpaceInfo:
    platform: str
    id: str
    slug: str
    role: str


@dataclass(frozen=True)
class RelatedRepository:
    repo: str
    boundary: str


@dataclass(frozen=True)
class SourceThread:
    id: str
    manifest_id: str | None
    platform: str
    date: str
    title: str
    turns: int
    preservation_report: str | None
    report_sha256: str | None
    scope_relevance: str
    notes: str


@dataclass(frozen=True)
class ExternalExport:
    manifest_id: str
    platform: str
    date: str
    title: str
    turns: int
    preservation_report: str
    report_sha256: str
    scope_relevance: str
    notes: str


@dataclass(frozen=True)
class ImportedDocument:
    id: str
    path: str
    sha256: str


@dataclass(frozen=True)
class UnrecoveredClaim:
    source: str
    claimed_artifact: str
    status: str
    mitigation: str


@dataclass(frozen=True)
class ComponentSpec:
    name: str
    module: str | None
    status: str


@dataclass(frozen=True)
class ProjectManifest:
    schema: str
    project: str
    description: str
    space: SpaceInfo
    related_repositories: tuple[RelatedRepository, ...]
    threads: tuple[SourceThread, ...]
    external_exports: tuple[ExternalExport, ...]
    imported_documents: tuple[ImportedDocument, ...]
    unrecovered_claims: tuple[UnrecoveredClaim, ...]
    components: tuple[ComponentSpec, ...]

    def summary_counts(self) -> dict[str, Any]:
        by_status: dict[str, int] = {}
        for comp in self.components:
            by_status[comp.status] = by_status.get(comp.status, 0) + 1
        return {
            "schema": self.schema,
            "project": self.project,
            "space_id": self.space.id,
            "threads": len(self.threads),
            "external_exports": len(self.external_exports),
            "imported_documents": len(self.imported_documents),
            "unrecovered_claims": len(self.unrecovered_claims),
            "components": len(self.components),
            "components_by_status": by_status,
        }


def _require_str(mapping: dict[str, Any], key: str, ctx: str) -> str:
    val = mapping.get(key)
    if not isinstance(val, str) or not val.strip():
        raise ManifestError(f"{ctx}: missing or empty string '{key}'")
    return val


def _validate_uuid(value: str, ctx: str) -> str:
    if not _UUID_RE.match(value):
        raise ManifestError(f"{ctx}: invalid canonical lowercase UUID '{value}'")
    return value


def _validate_sha256(value: str, ctx: str) -> str:
    if not _SHA256_RE.match(value):
        raise ManifestError(f"{ctx}: invalid sha256 digest '{value}'")
    return value


def parse_manifest(raw: dict[str, Any]) -> ProjectManifest:
    if not isinstance(raw, dict):
        raise ManifestError("manifest root must be a JSON object")
    schema = _require_str(raw, "schema", "manifest")
    if schema != EXPECTED_SCHEMA:
        raise ManifestError(
            f"manifest: unsupported schema '{schema}' (expected '{EXPECTED_SCHEMA}')"
        )

    project = _require_str(raw, "project", "manifest")
    description = _require_str(raw, "description", "manifest")

    space_raw = raw.get("space")
    if not isinstance(space_raw, dict):
        raise ManifestError("manifest.space must be an object")
    space = SpaceInfo(
        platform=_require_str(space_raw, "platform", "space"),
        id=_validate_uuid(_require_str(space_raw, "id", "space"), "space.id"),
        slug=_require_str(space_raw, "slug", "space"),
        role=_require_str(space_raw, "role", "space"),
    )

    repos_raw = raw.get("related_repositories", [])
    if not isinstance(repos_raw, list):
        raise ManifestError("manifest.related_repositories must be a list")
    related_repos: list[RelatedRepository] = []
    for idx, entry in enumerate(repos_raw):
        ctx = f"related_repositories[{idx}]"
        if not isinstance(entry, dict):
            raise ManifestError(f"{ctx} must be an object")
        related_repos.append(
            RelatedRepository(
                repo=_require_str(entry, "repo", ctx),
                boundary=_require_str(entry, "boundary", ctx),
            )
        )

    threads_raw = raw.get("threads")
    if not isinstance(threads_raw, list) or not threads_raw:
        raise ManifestError("manifest.threads must be a non-empty list")

    seen_uuids: set[str] = set()
    seen_manifest_ids: set[str] = set()
    threads: list[SourceThread] = []
    for idx, entry in enumerate(threads_raw):
        ctx = f"threads[{idx}]"
        if not isinstance(entry, dict):
            raise ManifestError(f"{ctx} must be an object")
        tuuid = _validate_uuid(_require_str(entry, "id", ctx), f"{ctx}.id")
        if tuuid in seen_uuids:
            raise ManifestError(f"{ctx}: duplicate thread UUID '{tuuid}'")
        seen_uuids.add(tuuid)

        mid = entry.get("manifest_id")
        if mid is not None:
            if not isinstance(mid, str) or not mid.strip():
                raise ManifestError(f"{ctx}: invalid manifest_id")
            if mid in seen_manifest_ids:
                raise ManifestError(f"{ctx}: duplicate manifest_id '{mid}'")
            seen_manifest_ids.add(mid)

        turns = entry.get("turns")
        if not isinstance(turns, int) or turns < 1:
            raise ManifestError(f"{ctx}: 'turns' must be a positive integer")

        pres_report = entry.get("preservation_report")
        rep_sha = entry.get("report_sha256")
        if pres_report is not None and not isinstance(pres_report, str):
            raise ManifestError(f"{ctx}: invalid preservation_report")
        if rep_sha is not None:
            if not isinstance(rep_sha, str):
                raise ManifestError(f"{ctx}: invalid report_sha256")
            _validate_sha256(rep_sha, f"{ctx}.report_sha256")

        rel = _require_str(entry, "scope_relevance", ctx)
        if rel not in VALID_SCOPE_RELEVANCE:
            raise ManifestError(f"{ctx}: invalid scope_relevance '{rel}'")

        threads.append(
            SourceThread(
                id=tuuid,
                manifest_id=mid,
                platform=_require_str(entry, "platform", ctx),
                date=_require_str(entry, "date", ctx),
                title=_require_str(entry, "title", ctx),
                turns=turns,
                preservation_report=pres_report,
                report_sha256=rep_sha,
                scope_relevance=rel,
                notes=_require_str(entry, "notes", ctx),
            )
        )

    exports_raw = raw.get("external_exports", [])
    if not isinstance(exports_raw, list):
        raise ManifestError("manifest.external_exports must be a list")
    external_exports: list[ExternalExport] = []
    for idx, entry in enumerate(exports_raw):
        ctx = f"external_exports[{idx}]"
        if not isinstance(entry, dict):
            raise ManifestError(f"{ctx} must be an object")
        mid = _require_str(entry, "manifest_id", ctx)
        if mid in seen_manifest_ids:
            raise ManifestError(f"{ctx}: duplicate manifest_id '{mid}'")
        seen_manifest_ids.add(mid)
        turns = entry.get("turns")
        if not isinstance(turns, int) or turns < 1:
            raise ManifestError(f"{ctx}: 'turns' must be a positive integer")
        rel = _require_str(entry, "scope_relevance", ctx)
        if rel not in VALID_SCOPE_RELEVANCE:
            raise ManifestError(f"{ctx}: invalid scope_relevance '{rel}'")
        external_exports.append(
            ExternalExport(
                manifest_id=mid,
                platform=_require_str(entry, "platform", ctx),
                date=_require_str(entry, "date", ctx),
                title=_require_str(entry, "title", ctx),
                turns=turns,
                preservation_report=_require_str(entry, "preservation_report", ctx),
                report_sha256=_validate_sha256(
                    _require_str(entry, "report_sha256", ctx), f"{ctx}.report_sha256"
                ),
                scope_relevance=rel,
                notes=_require_str(entry, "notes", ctx),
            )
        )

    docs_raw = raw.get("imported_documents")
    if not isinstance(docs_raw, list) or not docs_raw:
        raise ManifestError("manifest.imported_documents must be a non-empty list")
    seen_doc_ids: set[str] = set()
    imported_docs: list[ImportedDocument] = []
    for idx, entry in enumerate(docs_raw):
        ctx = f"imported_documents[{idx}]"
        if not isinstance(entry, dict):
            raise ManifestError(f"{ctx} must be an object")
        did = _require_str(entry, "id", ctx)
        if did in seen_doc_ids:
            raise ManifestError(f"{ctx}: duplicate imported document id '{did}'")
        seen_doc_ids.add(did)
        imported_docs.append(
            ImportedDocument(
                id=did,
                path=_require_str(entry, "path", ctx),
                sha256=_validate_sha256(_require_str(entry, "sha256", ctx), f"{ctx}.sha256"),
            )
        )

    claims_raw = raw.get("unrecovered_claims", [])
    if not isinstance(claims_raw, list):
        raise ManifestError("manifest.unrecovered_claims must be a list")
    claims: list[UnrecoveredClaim] = []
    for idx, entry in enumerate(claims_raw):
        ctx = f"unrecovered_claims[{idx}]"
        if not isinstance(entry, dict):
            raise ManifestError(f"{ctx} must be an object")
        claims.append(
            UnrecoveredClaim(
                source=_require_str(entry, "source", ctx),
                claimed_artifact=_require_str(entry, "claimed_artifact", ctx),
                status=_require_str(entry, "status", ctx),
                mitigation=_require_str(entry, "mitigation", ctx),
            )
        )

    comps_raw = raw.get("components")
    if not isinstance(comps_raw, list) or not comps_raw:
        raise ManifestError("manifest.components must be a non-empty list")
    seen_comp_names: set[str] = set()
    components: list[ComponentSpec] = []
    for idx, entry in enumerate(comps_raw):
        ctx = f"components[{idx}]"
        if not isinstance(entry, dict):
            raise ManifestError(f"{ctx} must be an object")
        cname = _require_str(entry, "name", ctx)
        if cname in seen_comp_names:
            raise ManifestError(f"{ctx}: duplicate component name '{cname}'")
        seen_comp_names.add(cname)
        status = _require_str(entry, "status", ctx)
        if status not in VALID_COMPONENT_STATUSES:
            raise ManifestError(f"{ctx}: invalid status '{status}'")
        module = entry.get("module")
        if status == "implemented":
            if not isinstance(module, str) or not module.startswith("hand_script."):
                raise ManifestError(
                    f"{ctx}: implemented component must specify a 'hand_script.*' module"
                )
        elif module is not None:
            raise ManifestError(f"{ctx}: non-implemented component must set module to null")
        components.append(ComponentSpec(name=cname, module=module, status=status))

    return ProjectManifest(
        schema=schema,
        project=project,
        description=description,
        space=space,
        related_repositories=tuple(related_repos),
        threads=tuple(threads),
        external_exports=tuple(external_exports),
        imported_documents=tuple(imported_docs),
        unrecovered_claims=tuple(claims),
        components=tuple(components),
    )


def load_manifest(path: Path | None = None) -> ProjectManifest:
    if path is None:
        raw_text = (
            resources.files("hand_script.data")
            .joinpath("project_manifest.json")
            .read_text(encoding="utf-8")
        )
    else:
        raw_text = path.read_text(encoding="utf-8")
    return parse_manifest(json.loads(raw_text))


def verify_preserved_copies(
    manifest: ProjectManifest, repo_root: Path
) -> list[tuple[str, str, str]]:
    """Verify SHA-256 digests of `imported_documents` inside `repo_root`."""
    verified: list[tuple[str, str, str]] = []
    for doc in manifest.imported_documents:
        target = repo_root / doc.path
        if not target.is_file():
            raise ManifestError(f"imported document {doc.id}: file not found at '{doc.path}'")
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if digest != doc.sha256:
            raise ManifestError(
                f"imported document {doc.id}: sha256 mismatch for '{doc.path}' "
                f"(expected {doc.sha256}, got {digest})"
            )
        verified.append((doc.id, doc.path, digest))
    return verified
