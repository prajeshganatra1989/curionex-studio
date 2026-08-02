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
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
  retries: number;
  error_message: string | null;
  created_at: string;
};

export type AiGeneration = {
  id: string;
  job_id: string;
  prompt_version_id: string;
  model_id: string;
  provider_id: string;
  input_variables: Record<string, string>;
  output_text: string | null;
  tokens_input: number | null;
  tokens_output: number | null;
  cost_usd: number | null;
  latency_ms: number | null;
  temperature: number | null;
  seed: number | null;
  created_at: string;
};

export type AiSettings = {
  default_model_id: string | null;
  default_temperature: number;
  default_max_tokens: number;
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
  Pick<AiSettings, "default_model_id" | "default_temperature" | "default_max_tokens">
>;
