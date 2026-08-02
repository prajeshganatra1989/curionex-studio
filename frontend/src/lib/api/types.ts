export type ProjectStatus = "draft" | "active" | "archived";

export type Category = {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type Tag = {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  updated_at: string;
};

export type Project = {
  id: string;
  project_code: string;
  name: string;
  description: string | null;
  status: ProjectStatus | string;
  category_id: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
  category: Category | null;
  tags: Tag[];
};

export type ProjectListResponse = {
  items: Project[];
  page: number;
  page_size: number;
  total: number;
};

export type ProjectCreateInput = {
  name: string;
  description?: string | null;
  status?: ProjectStatus | string;
  category_id?: string | null;
  tag_ids?: string[];
};

export type ProjectUpdateInput = {
  name?: string;
  description?: string | null;
  status?: ProjectStatus | string;
  category_id?: string | null;
  tag_ids?: string[];
};

export type ProjectListParams = {
  page?: number;
  page_size?: number;
  status?: string;
  category_id?: string;
  tag_id?: string;
  created_by?: string;
  search?: string;
};

export type CategoryCreateInput = {
  name: string;
  slug?: string | null;
  description?: string | null;
  is_active?: boolean;
};

export type TagCreateInput = {
  name: string;
  slug?: string | null;
};

export type KnowledgePackSummary = {
  id: string;
  project_id: string;
  name: string;
  description: string | null;
  status: string;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type KnowledgePackSection = {
  id: string;
  knowledge_pack_id: string;
  section_key: string;
  title: string;
  content: string;
  position: number;
  created_at: string;
  updated_at: string;
};

export type KnowledgePackDetail = KnowledgePackSummary & {
  sections: KnowledgePackSection[];
};

export type KnowledgePackSectionUpdateInput = {
  title?: string;
  content?: string;
};

export type KnowledgePackListResponse = {
  items: KnowledgePackSummary[];
  page: number;
  page_size: number;
  total: number;
};

export type KnowledgePackCreateInput = {
  name: string;
  description?: string | null;
  status?: string;
};

export type ScriptStatus =
  | "draft"
  | "in_progress"
  | "in_review"
  | "approved"
  | "archived"
  | string;

export type ScriptDocumentType =
  | "discovery_brief"
  | "story_spine"
  | "master_script";

export type ScriptSummary = {
  id: string;
  project_id: string;
  knowledge_pack_id: string | null;
  script_code: string;
  title: string;
  description: string | null;
  status: ScriptStatus;
  content_version_id: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type ScriptDocument = {
  id: string;
  script_id: string;
  document_type: ScriptDocumentType | string;
  title: string;
  content: string;
  position: number;
  created_at: string;
  updated_at: string;
};

export type ScriptDetail = ScriptSummary & {
  documents: ScriptDocument[];
};

export type ScriptListResponse = {
  items: ScriptSummary[];
  page: number;
  page_size: number;
  total: number;
};

export type ScriptListParams = {
  page?: number;
  page_size?: number;
  status?: string;
  search?: string;
};

export type ScriptCreateInput = {
  title: string;
  description?: string | null;
  knowledge_pack_id?: string | null;
};

export type ScriptUpdateInput = {
  title?: string;
  description?: string | null;
  knowledge_pack_id?: string | null;
  status?: ScriptStatus;
};

export type ScriptDocumentUpdateInput = {
  title?: string;
  content?: string;
};

export type ContentVersionSummary = {
  id: string;
  project_id: string;
  version_number: number;
  status: string;
  title: string;
  content: string;
  created_by: string;
  created_at: string;
};

export type ContentVersionListResponse = {
  items: ContentVersionSummary[];
  page: number;
  page_size: number;
  total: number;
};

export type WorkflowVersionRef = {
  id: string;
  version_number: number;
  status: string;
  title: string;
};

export type WorkflowVersionSummary = WorkflowVersionRef & {
  created_at: string;
};

export type WorkflowApprovalSummary = {
  id: string;
  status: string;
  content_version_id: string;
  created_at: string;
  reviewed_at: string | null;
};

export type WorkflowScriptSummary = {
  id: string;
  script_code: string;
  title: string;
  status: string;
  knowledge_pack_id: string | null;
  project_id: string;
};

export type ContentWorkflow = {
  id: string;
  script_id: string;
  current_stage: string;
  status: string;
  active_content_version_id: string | null;
  created_at: string;
  updated_at: string;
  script: WorkflowScriptSummary | null;
  knowledge_pack_id: string | null;
  active_content_version: WorkflowVersionSummary | null;
  latest_approval: WorkflowApprovalSummary | null;
};

export type WorkflowStatus = {
  script_id: string;
  stage: string;
  status: string;
  active_version: WorkflowVersionRef | null;
  latest_version: WorkflowVersionRef | null;
  approved_version: WorkflowVersionRef | null;
  pending_approval: WorkflowApprovalSummary | null;
};

export type WorkflowVersionCreateResponse = {
  workflow: ContentWorkflow;
  content_version: WorkflowVersionSummary;
};

export type WorkflowReviewResponse = {
  workflow: ContentWorkflow;
  approval: WorkflowApprovalSummary;
  content_version: WorkflowVersionSummary;
};

export type WorkflowStage =
  | "workspace"
  | "versioning"
  | "review"
  | "completed"
  | string;

export type WorkflowStatusValue =
  | "active"
  | "blocked"
  | "completed"
  | "archived"
  | string;
