export type ContentStandardStatus = "draft" | "active" | "archived" | string;

export type ContentStandard = {
  id: string;
  name: string;
  version: string;
  status: ContentStandardStatus;
  mission: string;
  target_audience: string;
  brand_voice: string;
  editorial_principles: string;
  hook_rules: string;
  story_structure: string;
  fact_policy: string;
  citation_policy: string;
  tone_guidelines: string;
  language_rules: string;
  forbidden_patterns: string;
  approved_cta_patterns: string;
  quality_checklist: string;
  default_duration_seconds: number;
  default_target_words: number;
  notes: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
};

export type ContentStandardSummary = {
  id: string | null;
  name: string | null;
  version: string | null;
  status: string | null;
  label: string | null;
  updated_at: string | null;
  has_active: boolean;
};

export type ContentStandardListResponse = {
  items: ContentStandard[];
  total: number;
};
