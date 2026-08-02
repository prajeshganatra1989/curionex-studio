/** Metric availability — never mix failure with a silent zero. */
export type MetricAvailability = "live" | "unavailable" | "restricted";

export type MetricValue = {
  value: number | null;
  availability: MetricAvailability;
};

export type DashboardMetrics = {
  projects: MetricValue;
  knowledgePacks: MetricValue;
  scripts: MetricValue;
  draftScripts: MetricValue;
  needingRevision: MetricValue;
  pendingReviews: MetricValue;
  approvedScripts: MetricValue;
  aiRunning: MetricValue;
  aiFailed: MetricValue;
  averageQualityScore: MetricValue;
  staleQualityReviews: MetricValue;
};

export type DailyGoal = {
  label: string;
  completed: number;
  target: number;
  remaining: number;
  completionPercent: number;
  weeklyCompleted: number;
  weeklyTarget: number;
  availability: MetricAvailability;
};

export type RecentProject = {
  id: string;
  projectCode: string;
  name: string;
  category: string | null;
  status: string;
  updatedAt: string;
};

export type RecentScript = {
  id: string;
  projectId: string;
  title: string;
  projectCode: string;
  status: string;
  updatedAt: string;
};

export type PendingReview = {
  id: string;
  title: string;
  versionNumber: number;
  status: string;
  reviewerInitials: string | null;
  updatedAt: string;
  projectCode?: string;
  scriptCode?: string | null;
};

export type RecentActivity = {
  id: string;
  action: string;
  summary: string;
  actorName: string;
  createdAt: string;
};

export type PanelAvailability = MetricAvailability | "empty";

export type DashboardData = {
  metrics: DashboardMetrics;
  dailyGoal: DailyGoal;
  recentProjects: RecentProject[];
  recentProjectsAvailability: MetricAvailability;
  recentScripts: RecentScript[];
  recentScriptsAvailability: MetricAvailability;
  pendingReviews: PendingReview[];
  pendingReviewsAvailability: MetricAvailability;
  recentActivity: RecentActivity[];
  recentActivityAvailability: MetricAvailability;
};
