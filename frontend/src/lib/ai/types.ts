export type AiProvider = {
  id: string;
  code: string;
  name: string;
  is_active: boolean;
  base_url: string | null;
  has_credentials: boolean;
  created_at: string;
  updated_at: string;
};

export type AiModel = {
  id: string;
  provider_id: string;
  code: string;
  name: string;
  context_window: number | null;
  supports_reasoning: boolean;
  supports_streaming: boolean;
  is_active: boolean;
  is_default: boolean;
  pricing_input_per_1k: number | null;
  pricing_output_per_1k: number | null;
};

export type AiPromptStatus = "draft" | "active" | "archived" | string;

export type AiPromptVersion = {
  id: string;
  prompt_id: string;
  version_number: number;
  system_prompt: string;
  user_template: string;
  variables: string[];
  status: string;
  created_by: string;
  created_at: string;
};

export type AiPrompt = {
  id: string;
  name: string;
  description: string | null;
  purpose: string | null;
  status: AiPromptStatus;
  owner_id: string;
  active_version_id: string | null;
  created_at: string;
  updated_at: string;
  active_version?: AiPromptVersion;
};

export type AiJobStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled"
  | string;

export type AiJob = {
  id: string;
  status: AiJobStatus;
  requested_by: string;
  prompt_version_id: string;
  model_id: string;
  input_variables: Record<string, string>;
  /** Set for purpose-built jobs, e.g. "knowledge_pack.draft". */
  purpose?: string | null;
  knowledge_pack_id?: string | null;
  project_id?: string | null;
  script_id?: string | null;
  document_type?: string | null;
  idempotency_key?: string | null;
  cancel_requested?: boolean;
  /** Present when a completed job already has a generation row. */
  generation_id?: string | null;
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
  retries: number;
  error_message: string | null;
  created_at: string;
};

/** Script Document types that support AI drafting. */
export type ScriptAiDocumentType =
  | "discovery_brief"
  | "story_spine"
  | "master_script";

export const SCRIPT_AI_DOCUMENT_TYPES: ScriptAiDocumentType[] = [
  "discovery_brief",
  "story_spine",
  "master_script",
];

export const SCRIPT_AI_PURPOSE_BY_DOCUMENT: Record<
  ScriptAiDocumentType,
  string
> = {
  discovery_brief: "script.discovery_brief.draft",
  story_spine: "script.story_spine.draft",
  master_script: "script.master_script.draft",
};

export type ScriptAiConflictStrategy =
  | "reject_if_non_empty"
  | "replace"
  | "append";

/** A single reference cited by an AI draft. Always unverified — never trust as fact. */
export type KnowledgePackDraftSource = {
  label: string;
  reference: string;
  verification_status: "unverified";
};

/** Structured Knowledge Pack draft returned by the OpenAI Responses API. */
export type KnowledgePackDraft = {
  research: string;
  facts: string[];
  sources: KnowledgePackDraftSource[];
  audience: string;
  content_angle: string;
  key_insights: string[];
  additional_context: string;
  warnings: string[];
};

export type KnowledgePackApplyableSection =
  | "research"
  | "facts"
  | "sources"
  | "audience"
  | "content_angle"
  | "key_insights"
  | "additional_context";

export const KNOWLEDGE_PACK_APPLYABLE_SECTIONS: KnowledgePackApplyableSection[] = [
  "research",
  "facts",
  "sources",
  "audience",
  "content_angle",
  "key_insights",
  "additional_context",
];

export type KnowledgePackConflictStrategy =
  | "reject_if_non_empty"
  | "replace_selected"
  | "append_selected";

export type AiGeneration = {
  id: string;
  job_id: string;
  prompt_version_id: string;
  model_id: string;
  provider_id: string;
  input_variables: Record<string, string>;
  output_text: string | null;
  /** Present for structured-output jobs, e.g. Knowledge Pack drafts. */
  structured_output?: KnowledgePackDraft | Record<string, unknown> | null;
  purpose?: string | null;
  knowledge_pack_id?: string | null;
  project_id?: string | null;
  script_id?: string | null;
  document_type?: string | null;
  tokens_input: number | null;
  tokens_output: number | null;
  tokens_total?: number | null;
  cost_usd: number | null;
  latency_ms: number | null;
  provider_request_id?: string | null;
  model_identifier?: string | null;
  temperature: number | null;
  seed: number | null;
  /** Section keys already applied to a Knowledge Pack from this generation. */
  applied_sections?: string[];
  applied_at?: string | null;
  warnings?: string[];
  input_fingerprint?: Record<string, unknown> | null;
  stale_input?: boolean | null;
  created_at: string;
};

export type AiSettings = {
  default_model_id: string | null;
  default_temperature: number;
  default_max_tokens: number;
  brand_voice?: string | null;
  quality_requirements?: string | null;
  default_target_duration_seconds?: number;
  default_target_words_per_minute?: number;
  [key: string]: unknown;
};

export type PaginatedResponse<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
};

export type AiPromptListParams = {
  page?: number;
  page_size?: number;
  status?: string;
  search?: string;
};

export type AiJobListParams = {
  page?: number;
  page_size?: number;
  status?: string;
};

export type AiGenerationListParams = {
  page?: number;
  page_size?: number;
  project_id?: string;
  script_id?: string;
  document_type?: string;
  purpose?: string;
  provider_id?: string;
  model_id?: string;
  /** When set, filter to generations that have / have not been applied. */
  applied?: boolean;
};

export type AiPromptCreateInput = {
  name: string;
  description?: string | null;
  purpose?: string | null;
  system_prompt: string;
  user_template: string;
  variables: string[];
};

export type AiPromptUpdateInput = {
  name?: string;
  description?: string | null;
  purpose?: string | null;
  status?: AiPromptStatus;
};

export type AiPromptVersionCreateInput = {
  system_prompt: string;
  user_template: string;
  variables: string[];
};

export type AiProviderUpdateInput = {
  is_active?: boolean;
  base_url?: string | null;
};

export type AiProviderCredentialsInput = {
  api_key: string;
};

export type AiModelUpdateInput = {
  is_active?: boolean;
  is_default?: boolean;
};

export type AiJobCreateInput = {
  prompt_id: string;
  model_id: string;
  input_variables: Record<string, string>;
};

export type AiSettingsUpdateInput = Partial<
  Pick<
    AiSettings,
    | "default_model_id"
    | "default_temperature"
    | "default_max_tokens"
    | "brand_voice"
    | "quality_requirements"
    | "default_target_duration_seconds"
    | "default_target_words_per_minute"
  >
>;

export type ScriptAiDraftCreateInput = {
  model_id?: string | null;
  language: string;
  tone: string;
  target_duration_seconds?: number | null;
  target_words_per_minute?: number | null;
  idempotency_key?: string | null;
};

export type ScriptAiDraftApplyInput = {
  conflict_strategy: ScriptAiConflictStrategy;
};

export type ScriptAiDraftApplyResponse = {
  document: {
    id: string;
    script_id: string;
    document_type: string;
    title: string;
    content: string;
    position: number;
    created_at: string;
    updated_at: string;
  };
  generation_id: string;
  conflict_strategy: ScriptAiConflictStrategy;
  stale_input: boolean;
};

export type ScriptAiPrerequisitesResponse = {
  document_type: string;
  ready: boolean;
  missing: string[];
};

/** Structured 409 conflict detail when applying to a non-empty script document. */
export type ScriptAiDraftConflictDetail = {
  message: string;
  conflicts?: string[];
};

export type KnowledgePackAiDraftCreateInput = {
  model_id?: string | null;
  target_audience?: string;
  language?: string;
  desired_depth?: string;
  idempotency_key?: string | null;
};

export type KnowledgePackAiDraftApplyInput = {
  sections: string[];
  conflict_strategy: KnowledgePackConflictStrategy;
};

export type KnowledgePackAiDraftApplyResponse = {
  knowledge_pack: {
    id: string;
    project_id: string;
    name: string;
    description: string | null;
    status: string;
    created_by: string;
    created_at: string;
    updated_at: string;
    sections: {
      id: string;
      knowledge_pack_id: string;
      section_key: string;
      title: string;
      content: string;
      position: number;
      created_at: string;
      updated_at: string;
    }[];
  };
  generation_id: string;
  applied_sections: string[];
  conflict_strategy: KnowledgePackConflictStrategy;
};

/** Structured 409 conflict detail returned when applying to non-empty sections. */
export type KnowledgePackAiDraftConflictDetail = {
  message: string;
  conflicts: string[];
};
