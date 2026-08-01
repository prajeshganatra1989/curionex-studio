"""Controlled Knowledge Pack section catalog.

Section rows are stored in ``knowledge_pack_sections`` — never as columns on
``knowledge_packs``. New section types can be appended to this catalog later.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SectionDefinition:
    """Stable machine-readable section key with display metadata."""

    key: str
    title: str
    description: str
    position: int


SECTION_CATALOG: tuple[SectionDefinition, ...] = (
    SectionDefinition(
        key="research",
        title="Research",
        description="Research and background information",
        position=1,
    ),
    SectionDefinition(
        key="facts",
        title="Facts",
        description="Verified factual information",
        position=2,
    ),
    SectionDefinition(
        key="sources",
        title="Sources",
        description="Sources and references used during research",
        position=3,
    ),
    SectionDefinition(
        key="audience",
        title="Audience",
        description="Intended audience information",
        position=4,
    ),
    SectionDefinition(
        key="content_angle",
        title="Content angle",
        description="Core angle or perspective of the content",
        position=5,
    ),
    SectionDefinition(
        key="key_insights",
        title="Key insights",
        description="Important insights and takeaways",
        position=6,
    ),
    SectionDefinition(
        key="additional_context",
        title="Additional context",
        description="Additional context that does not fit other sections",
        position=7,
    ),
)

SECTION_KEYS: frozenset[str] = frozenset(item.key for item in SECTION_CATALOG)

SECTION_BY_KEY: dict[str, SectionDefinition] = {
    item.key: item for item in SECTION_CATALOG
}


def initial_section_definitions() -> tuple[SectionDefinition, ...]:
    """Return the default section shells created with every Knowledge Pack."""
    return SECTION_CATALOG
