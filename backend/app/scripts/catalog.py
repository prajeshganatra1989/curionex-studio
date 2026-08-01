"""Controlled ScriptDocument type catalog."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DocumentDefinition:
    document_type: str
    title: str
    description: str
    position: int


DOCUMENT_CATALOG: tuple[DocumentDefinition, ...] = (
    DocumentDefinition(
        document_type="discovery_brief",
        title="Discovery Brief",
        description="Structured discovery brief for the script workspace",
        position=1,
    ),
    DocumentDefinition(
        document_type="story_spine",
        title="Story Spine",
        description="Narrative spine and story structure",
        position=2,
    ),
    DocumentDefinition(
        document_type="master_script",
        title="Master Script",
        description="Full master script draft",
        position=3,
    ),
)

DOCUMENT_TYPES: frozenset[str] = frozenset(
    item.document_type for item in DOCUMENT_CATALOG
)

DOCUMENT_BY_TYPE: dict[str, DocumentDefinition] = {
    item.document_type: item for item in DOCUMENT_CATALOG
}


def initial_document_definitions() -> tuple[DocumentDefinition, ...]:
    return DOCUMENT_CATALOG
