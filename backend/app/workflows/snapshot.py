"""Deterministic workspace → ContentVersion snapshot builder."""

from __future__ import annotations

from collections.abc import Sequence

from app.models.script import ScriptDocument
from app.scripts.catalog import DOCUMENT_CATALOG

# Fixed section order for snapshot determinism (independent of DB insertion order).
SNAPSHOT_DOCUMENT_ORDER: tuple[str, ...] = tuple(
    item.document_type for item in DOCUMENT_CATALOG
)

SNAPSHOT_SECTION_HEADERS: dict[str, str] = {
    "discovery_brief": "DISCOVERY BRIEF",
    "story_spine": "STORY SPINE",
    "master_script": "MASTER SCRIPT",
}


class SnapshotValidationError(ValueError):
    """Raised when required workspace documents are missing."""


def build_workspace_snapshot(documents: Sequence[ScriptDocument]) -> str:
    """Build a plain-text ContentVersion snapshot from ScriptDocuments.

    Order is always discovery_brief → story_spine → master_script.
    """
    by_type = {doc.document_type: doc for doc in documents}
    missing = [doc_type for doc_type in SNAPSHOT_DOCUMENT_ORDER if doc_type not in by_type]
    if missing:
        raise SnapshotValidationError(
            "Missing required workspace documents: " + ", ".join(missing)
        )

    parts: list[str] = []
    for doc_type in SNAPSHOT_DOCUMENT_ORDER:
        document = by_type[doc_type]
        parts.append(SNAPSHOT_SECTION_HEADERS[doc_type])
        parts.append("")
        parts.append(document.content or "")
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"
