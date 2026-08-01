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
  /** Short description shown under the section title. */
  description: string;
  /** Empty-state writing guidance. */
  guidance: string;
};

export const SECTION_ORDER: SectionMeta[] = [
  {
    key: "research",
    title: "Research",
    description: "Research and background information",
    guidance: "Collect raw information from trusted sources.",
  },
  {
    key: "facts",
    title: "Facts",
    description: "Verified factual information",
    guidance: "List verified facts only.",
  },
  {
    key: "sources",
    title: "Sources",
    description: "Sources and references used during research",
    guidance: "Record URLs, books or papers.",
  },
  {
    key: "audience",
    title: "Audience",
    description: "Intended audience information",
    guidance: "Describe who this video is for and what they already know.",
  },
  {
    key: "content_angle",
    title: "Content Angle",
    description: "Core angle or perspective of the content",
    guidance: "Define the unique angle that makes this video worth watching.",
  },
  {
    key: "key_insights",
    title: "Key Insights",
    description: "Important insights and takeaways",
    guidance: "Capture the insights viewers should remember.",
  },
  {
    key: "additional_context",
    title: "Additional Context",
    description: "Additional context that does not fit other sections",
    guidance: "Add anything else that supports the script later.",
  },
];

export const SECTION_BY_KEY: Record<SectionKey, SectionMeta> = Object.fromEntries(
  SECTION_ORDER.map((item) => [item.key, item]),
) as Record<SectionKey, SectionMeta>;
