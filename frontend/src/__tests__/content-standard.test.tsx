import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { EditorialSettingsPage } from "@/components/editorial/editorial-settings-page";
import { ContentStandardUsageBadge } from "@/components/editorial/content-standard-usage-badge";
import { ApiError } from "@/lib/api/client";
import type { ContentStandard } from "@/lib/editorial/content-standard-types";

const getActive = vi.fn();
const getSummary = vi.fn();

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

vi.mock("@/lib/api/content-standards", () => ({
  getActiveContentStandard: (...args: unknown[]) => getActive(...args),
  getContentStandardSummary: (...args: unknown[]) => getSummary(...args),
  listContentStandards: vi.fn(),
  getContentStandard: vi.fn(),
}));

vi.mock("@/lib/auth/auth-context", () => ({
  useAuth: () => ({
    status: "authenticated",
    user: {
      id: "user-1",
      email: "user@example.com",
      first_name: "Test",
      last_name: "User",
      is_active: true,
      created_at: "",
      updated_at: "",
    },
    login: vi.fn(),
    logout: vi.fn(),
    api: { baseUrl: "http://test" },
  }),
}));

const standard: ContentStandard = {
  id: "std-1",
  name: "Curionex Content Standard",
  version: "1",
  status: "active",
  mission: "Explain fascinating topics with clarity, curiosity and credibility.",
  target_audience: "General audience, 13+",
  brand_voice: "Friendly, confident, conversational",
  editorial_principles: "One memorable idea",
  hook_rules: "Create curiosity immediately",
  story_structure: "Hook → Context → Explanation → Twist → Payoff → CTA",
  fact_policy: "Never invent statistics",
  citation_policy: "Prefer authoritative sources",
  tone_guidelines: "Natural spoken English",
  language_rules: "Write for the ear",
  forbidden_patterns: "Clickbait promises",
  approved_cta_patterns: "Follow for more fascinating facts.",
  quality_checklist: "Curiosity\nClarity",
  default_duration_seconds: 60,
  default_target_words: 160,
  notes: null,
  created_by: "user-1",
  created_at: "2026-08-01T00:00:00Z",
  updated_at: "2026-08-01T00:00:00Z",
};

function wrap(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>{ui}</QueryClientProvider>,
  );
}

describe("Editorial Content Standard UI", () => {
  beforeEach(() => {
    getActive.mockReset();
    getSummary.mockReset();
  });

  it("renders editorial settings with version badge and preview", async () => {
    getActive.mockResolvedValue(standard);
    wrap(<EditorialSettingsPage />);
    expect(await screen.findByTestId("editorial-settings")).toBeInTheDocument();
    expect(screen.getByTestId("content-standard-version-badge")).toHaveTextContent(
      "v1",
    );
    expect(screen.getByTestId("content-standard-preview")).toBeInTheDocument();
    expect(screen.getByText(/Explain fascinating topics/)).toBeInTheDocument();
  });

  it("shows empty state when no active standard", async () => {
    getActive.mockRejectedValue(new ApiError(404, "No active content standard."));
    wrap(<EditorialSettingsPage />);
    expect(
      await screen.findByTestId("content-standard-empty"),
    ).toBeInTheDocument();
    expect(screen.getByText("No active Content Standard")).toBeInTheDocument();
  });

  it("shows prompt usage badge for active standard", async () => {
    getSummary.mockResolvedValue({
      id: "std-1",
      name: "Curionex Content Standard",
      version: "1",
      status: "active",
      label: "Curionex Content Standard v1",
      updated_at: "2026-08-01T00:00:00Z",
      has_active: true,
    });
    wrap(<ContentStandardUsageBadge />);
    expect(
      await screen.findByText("Curionex Content Standard v1"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("content-standard-usage")).toHaveTextContent(
      "Uses: Curionex Content Standard v1",
    );
  });
});
