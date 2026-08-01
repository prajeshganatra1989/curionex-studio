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

export type ScriptSummary = {
  id: string;
  project_id: string;
  knowledge_pack_id: string | null;
  script_code: string;
  title: string;
  description: string | null;
  status: string;
  content_version_id: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type ScriptListResponse = {
  items: ScriptSummary[];
  page: number;
  page_size: number;
  total: number;
};

export type ScriptCreateInput = {
  title: string;
  description?: string | null;
  knowledge_pack_id?: string | null;
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

export type WorkflowVersionRef = {
  id: string;
  version_number: number;
  status: string;
  title: string;
};

export type WorkflowStatus = {
  script_id: string;
  stage: string;
  status: string;
  active_version: WorkflowVersionRef | null;
  latest_version: WorkflowVersionRef | null;
  approved_version: WorkflowVersionRef | null;
  pending_approval: {
    id: string;
    status: string;
    content_version_id: string;
    created_at: string;
    reviewed_at: string | null;
  } | null;
};
