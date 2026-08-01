/** Frontend section catalog — mirrors backend SECTION_CATALOG display order. */

export type SectionKey =
  | "research"
  | "facts"
  | "sources"
  | "audience"
  | "content_angle"
  | "key_insights"
  | "additional_context";

export type SectionMeta = {
  key: SectionKey;
  title: string;
  /** Short helper description under the title. */
  description: string;
  /** Empty-state / placeholder guidance. */
  guidance: string;
};

export const SECTION_ORDER: SectionMeta[] = [
  {
    key: "research",
    title: "Research",
    description: "Collect everything useful.",
    guidance: "Collect everything useful from trusted notes and references.",
  },
  {
    key: "facts",
    title: "Facts",
    description: "Verified information only.",
    guidance: "List verified facts only.",
  },
  {
    key: "sources",
    title: "Sources",
    description: "Books · URLs · Papers",
    guidance: "Record books, URLs, or papers.",
  },
  {
    key: "audience",
    title: "Audience",
    description: "Who is this video for?",
    guidance: "Who is this video for?",
  },
  {
    key: "content_angle",
    title: "Content Angle",
    description: "What's the unique perspective?",
    guidance: "What's the unique perspective?",
  },
  {
    key: "key_insights",
    title: "Key Insights",
    description: "What should viewers remember?",
    guidance: "What should viewers remember?",
  },
  {
    key: "additional_context",
    title: "Additional Context",
    description: "Anything else useful.",
    guidance: "Anything else useful for scripting later.",
  },
];

export const SECTION_BY_KEY: Record<SectionKey, SectionMeta> = Object.fromEntries(
  SECTION_ORDER.map((item) => [item.key, item]),
) as Record<SectionKey, SectionMeta>;
