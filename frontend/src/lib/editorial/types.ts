export const TOPIC_STATUSES = [
  "idea",
  "planned",
  "in_progress",
  "project_created",
  "published",
  "archived",
] as const;

export type TopicStatus = (typeof TOPIC_STATUSES)[number];

export const TOPIC_DIFFICULTIES = ["easy", "medium", "hard"] as const;
export type TopicDifficulty = (typeof TOPIC_DIFFICULTIES)[number];

export const TOPIC_VIRAL = ["low", "medium", "high"] as const;
export type TopicViralPotential = (typeof TOPIC_VIRAL)[number];

export const TOPIC_PRIORITIES = ["A", "B", "C"] as const;
export type TopicPriority = (typeof TOPIC_PRIORITIES)[number];

export const PRODUCTION_WAVES = [1, 2, 3, 4] as const;
export type ProductionWave = (typeof PRODUCTION_WAVES)[number];

export const EDITORIAL_CATEGORIES = [
  "Human Brain",
  "Psychology",
  "Space",
  "Earth",
  "Science",
  "Technology",
  "History",
  "Animals",
  "Human Body",
  "Biology",
] as const;

export type LinkedProjectSummary = {
  id: string;
  project_code: string;
  name: string;
  status: string;
};

export type EditorialTopic = {
  id: string;
  slug: string;
  title: string;
  description: string | null;
  category: string;
  status: TopicStatus | string;
  difficulty: TopicDifficulty | string;
  evergreen_score: number;
  curiosity_score: number;
  viral_potential: TopicViralPotential | string;
  estimated_duration_seconds: number;
  target_audience: string | null;
  source: string | null;
  notes: string | null;
  linked_project_id: string | null;
  published_video_url: string | null;
  is_featured: boolean;
  priority: TopicPriority | string;
  production_wave: number;
  created_at: string;
  updated_at: string;
  linked_project: LinkedProjectSummary | null;
};

export type EditorialTopicListResponse = {
  items: EditorialTopic[];
  page: number;
  page_size: number;
  total: number;
};

export type EditorialTopicListParams = {
  page?: number;
  page_size?: number;
  status?: string;
  category?: string;
  difficulty?: string;
  priority?: string;
  production_wave?: number;
  min_evergreen_score?: number;
  search?: string;
  include_archived?: boolean;
  sort?: string;
};

export type EditorialTopicCreateInput = {
  title: string;
  slug?: string | null;
  description?: string | null;
  category: string;
  status?: string;
  difficulty?: string;
  evergreen_score?: number;
  curiosity_score?: number;
  viral_potential?: string;
  estimated_duration_seconds?: number;
  target_audience?: string | null;
  source?: string | null;
  notes?: string | null;
  is_featured?: boolean;
  published_video_url?: string | null;
  priority?: string;
  production_wave?: number;
};

export type EditorialTopicUpdateInput = Partial<EditorialTopicCreateInput>;

export type DuplicateTitleWarning = {
  similar_topic_id: string;
  similar_title: string;
  similar_slug: string;
};

export type EditorialTopicCreateResponse = {
  topic: EditorialTopic;
  duplicate_warning: DuplicateTitleWarning | null;
};

export type CreateProjectFromTopicInput = {
  name?: string | null;
  description?: string | null;
  category_id?: string | null;
  tag_ids?: string[];
};

export type CreateProjectFromTopicResponse = {
  topic: EditorialTopic;
  project: import("@/lib/api/types").Project;
};

export type EditorialTopicSummary = {
  available: number;
  in_progress: number;
  published: number;
  project_created: number;
  total_active: number;
  wave_1_remaining: number;
  wave_2_remaining: number;
  current_wave: number;
  approved_in_current_wave: number;
  remaining_in_wave: number;
};
