import type { ContentStandard } from "@/lib/editorial/content-standard-types";

type ContentStandardPreviewProps = {
  standard: ContentStandard;
};

const SECTIONS: { key: keyof ContentStandard; label: string }[] = [
  { key: "mission", label: "Mission" },
  { key: "target_audience", label: "Target audience" },
  { key: "brand_voice", label: "Brand voice" },
  { key: "editorial_principles", label: "Editorial principles" },
  { key: "hook_rules", label: "Hook rules" },
  { key: "story_structure", label: "Story structure" },
  { key: "fact_policy", label: "Fact policy" },
  { key: "citation_policy", label: "Citation policy" },
  { key: "tone_guidelines", label: "Tone" },
  { key: "language_rules", label: "Language rules" },
  { key: "forbidden_patterns", label: "Forbidden patterns" },
  { key: "approved_cta_patterns", label: "Approved CTAs" },
  { key: "quality_checklist", label: "Quality checklist" },
];

export function ContentStandardPreview({
  standard,
}: ContentStandardPreviewProps) {
  return (
    <div className="space-y-5 p-2" data-testid="content-standard-preview">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-lg font-semibold text-foreground">
          {standard.name}
        </h3>
        <span
          className="rounded-md bg-brand-orange/10 px-2 py-0.5 text-xs font-semibold text-brand-orange"
          data-testid="content-standard-preview-version"
        >
          v{standard.version}
        </span>
      </div>
      <p className="text-sm text-muted-foreground">
        Defaults: {standard.default_duration_seconds}s ·{" "}
        {standard.default_target_words} words
      </p>
      {SECTIONS.map(({ key, label }) => {
        const value = standard[key];
        if (typeof value !== "string" || !value.trim()) return null;
        return (
          <section key={key}>
            <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              {label}
            </h4>
            <p className="mt-1 whitespace-pre-wrap text-sm text-foreground">
              {value}
            </p>
          </section>
        );
      })}
    </div>
  );
}
