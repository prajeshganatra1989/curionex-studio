export type DashboardMetrics = {
  projects: number;
  knowledgePacks: number;
  scripts: number;
  draftScripts: number;
  pendingReviews: number;
  approvedScripts: number;
  /** True when any metric cards still use demo values. */
  isDemo: boolean;
  /** True when the Projects metric comes from GET /projects total. */
  projectsLive: boolean;
};

export type DailyGoal = {
  label: string;
  completed: number;
  target: number;
  /** When true, values are demo/mock — not live backend data. */
  isDemo: boolean;
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
};

export type RecentActivity = {
  id: string;
  action: string;
  summary: string;
  actorName: string;
  createdAt: string;
};

export type DashboardData = {
  metrics: DashboardMetrics;
  dailyGoal: DailyGoal;
  recentProjects: RecentProject[];
  recentProjectsLive: boolean;
  recentScripts: RecentScript[];
  pendingReviews: PendingReview[];
  recentActivity: RecentActivity[];
  activityRestricted: boolean;
};
