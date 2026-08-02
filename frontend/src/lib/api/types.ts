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
  script_id: string | null;
  version_number: number;
  status: string;
  title: string;
  content: string;
  created_by: string;
  created_at: string;
};

/** Version row without snapshot body (approval inbox / lists). */
export type ContentVersionBrief = {
  id: string;
  project_id: string;
  script_id: string | null;
  version_number: number;
  status: string;
  title: string;
  created_by: string;
  created_at: string;
};

export type UserBrief = {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
};

export type ProjectBrief = {
  id: string;
  project_code: string;
  name: string;
};

export type ScriptBrief = {
  id: string;
  script_code: string;
  title: string;
  project_id: string;
  knowledge_pack_id: string | null;
};

export type ApprovalSummary = {
  id: string;
  status: string;
  comment: string | null;
  created_at: string;
  reviewed_at: string | null;
  requested_by: UserBrief;
  reviewed_by: UserBrief | null;
  content_version: ContentVersionBrief;
  project: ProjectBrief;
  script: ScriptBrief | null;
};

export type ApprovalListResponse = {
  items: ApprovalSummary[];
  page: number;
  page_size: number;
  total: number;
};

export type ApprovalListParams = {
  page?: number;
  page_size?: number;
  status?: string;
  project_id?: string;
  search?: string;
};

export type ApprovalRecord = {
  id: string;
  content_version_id: string;
  requested_by: string;
  reviewed_by: string | null;
  status: string;
  comment: string | null;
  created_at: string;
  reviewed_at: string | null;
};

export type ApprovalDetail = {
  id: string;
  status: string;
  comment: string | null;
  created_at: string;
  reviewed_at: string | null;
  requested_by: UserBrief;
  reviewed_by: UserBrief | null;
  content_version: ContentVersionSummary;
  project: ProjectBrief;
  script: ScriptBrief | null;
  version_approvals: ApprovalRecord[];
};

export type ApprovalActionInput = {
  comment?: string | null;
};

export type ApprovalRejectInput = {
  comment: string;
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

/** Production package (planning export — no media). */
export type ProductionPackageEligibility = {
  eligible: boolean;
  reason: string;
  gold_gate: string | null;
  overall_score: number | null;
  script_status: string;
  has_approved_version: boolean;
};

export type ProductionPackageScenePurpose =
  | "hook"
  | "question"
  | "explanation"
  | "twist"
  | "perspective_shift"
  | "cta";

export type ProductionPackageStoryboardScene = {
  scene_number: number;
  time_range: string;
  start_seconds: number;
  end_seconds: number;
  narration: string;
  purpose: ProductionPackageScenePurpose;
  suggested_visual: string;
  suggested_motion: string;
  suggested_on_screen_text: string;
  transition: string;
};

export type ProductionPackageStoryboardV2Scene = {
  scene_number: number;
  start_time: number;
  end_time: number;
  duration: number;
  narration: string;
  scene_goal: string;
  viewer_emotion: string;
  visual_type: string;
  camera_movement: string;
  transition: string;
  animation_suggestion: string;
  on_screen_text: string;
  text_position: string;
  asset_required: string;
  music_mood: string;
  sound_effects: string;
  notes: string;
  purpose: ProductionPackageScenePurpose;
};

export type ProductionPackageShot = {
  shot_number: number;
  scene_number: number;
  asset_type: string;
  description: string;
  illustration: boolean;
  stock: boolean;
  diagram: boolean;
  animation: boolean;
  text_overlay: boolean;
  priority: "must" | "should" | "nice" | string;
};

export type ProductionPackageAssetItem = {
  id: string;
  label: string;
  category: string;
  required: boolean;
  notes: string | null;
};

export type ProductionPackageVoice = {
  estimated_duration_seconds: number;
  word_count: number;
  recommended_wpm: number;
  pause_markers: string[];
  emphasis_markers: string[];
  pronunciation_notes: string[];
  persona_hint: string;
};

export type ProductionPackageSubtitle = {
  index: number;
  start_seconds: number;
  end_seconds: number;
  text: string;
  lines: string[];
};

export type ProductionPackageYouTube = {
  title: string;
  description: string;
  keywords: string[];
  hashtags: string[];
  category: string;
  thumbnail_concept: string;
};

export type ProductionPackageQaItem = {
  id: string;
  domain: string;
  label: string;
  checked: boolean;
};

export type ProductionPackage = {
  project: {
    id: string;
    project_code: string;
    name: string;
    status: string;
    description: string | null;
  };
  script: {
    id: string;
    script_code: string;
    title: string;
    status: string;
    description: string | null;
    knowledge_pack_id: string | null;
    project_id: string;
  };
  knowledge_pack: {
    id: string | null;
    name: string | null;
    status: string | null;
    description: string | null;
    facts: string | null;
    sources: string | null;
    content_angle: string | null;
    key_insights: string | null;
  };
  discovery_brief: string;
  story_spine: string;
  master_script: string;
  quality_review: {
    available: boolean;
    generation_id: string | null;
    overall_score: number | null;
    quality_band: string | null;
    recommended_next_action: string | null;
    gold_threshold_met: boolean;
  };
  production_metadata: {
    generated_at: string;
    gold_gate: string;
    target_duration_seconds: number;
    recommended_wpm: number;
    format: string;
    blueprint_version: string;
    voice_bible_version: string;
    editorial_bible_version: string;
    notes: string;
  };
  storyboard: ProductionPackageStoryboardScene[];
  storyboard_v2: ProductionPackageStoryboardV2Scene[];
  shot_list: ProductionPackageShot[];
  asset_checklist: ProductionPackageAssetItem[];
  voice_package: ProductionPackageVoice;
  subtitle_package: ProductionPackageSubtitle[];
  youtube_package: ProductionPackageYouTube;
  qa_package: ProductionPackageQaItem[];
};
