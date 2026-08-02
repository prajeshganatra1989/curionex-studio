import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { LoginForm } from "@/components/auth/login-form";
import { StatusBadge } from "@/components/ui/status-badge";
import { DailyGoalCard } from "@/components/dashboard/daily-goal-card";
import { MetricCard } from "@/components/dashboard/metric-card";
import { RecentProjectsList } from "@/components/dashboard/recent-projects-list";
import { RecentScriptsList } from "@/components/dashboard/recent-scripts-list";
import { PendingReviewsList } from "@/components/dashboard/pending-reviews-list";
import { ActivityTimeline } from "@/components/dashboard/activity-timeline";
import { EmptyState } from "@/components/ui/empty-state";
import { SidebarNavigation } from "@/components/layout/sidebar-navigation";
import { tokenStore } from "@/lib/auth/token-store";
import { statusLabel } from "@/lib/status";
import { FolderKanban } from "lucide-react";

const replaceMock = vi.fn();
const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock, push: pushMock }),
  usePathname: () => "/dashboard",
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("next/image", () => ({
  // Test stub — avoid next/image in jsdom.
  default: (props: { alt: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img alt={props.alt} />
  ),
}));

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
    ...rest
  }: {
    children: React.ReactNode;
    href: string;
  }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

const loginMock = vi.fn();
const logoutMock = vi.fn();

vi.mock("@/lib/auth/auth-context", () => ({
  useAuth: () => ({
    status: "unauthenticated",
    user: null,
    login: loginMock,
    logout: logoutMock,
    api: {},
  }),
}));

function wrap(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>{ui}</QueryClientProvider>,
  );
}

describe("LoginForm", () => {
  beforeEach(() => {
    loginMock.mockReset();
    replaceMock.mockReset();
    tokenStore.clear();
  });

  it("renders email and password fields", () => {
    wrap(<LoginForm />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /sign in/i }),
    ).toBeInTheDocument();
  });

  it("validates empty submission", async () => {
    const user = userEvent.setup();
    wrap(<LoginForm />);
    await user.click(screen.getByRole("button", { name: /sign in/i }));
    expect(await screen.findByText(/valid email/i)).toBeInTheDocument();
    expect(loginMock).not.toHaveBeenCalled();
  });

  it("stores auth via login abstraction on success", async () => {
    const user = userEvent.setup();
    loginMock.mockImplementation(async () => {
      tokenStore.setAccessToken("test-token-value");
    });
    wrap(<LoginForm />);
    await user.type(screen.getByLabelText(/email/i), "owner@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "securepass123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));
    await waitFor(() => expect(loginMock).toHaveBeenCalled());
    expect(tokenStore.getAccessToken()).toBe("test-token-value");
    expect(document.body.textContent).not.toContain("test-token-value");
    expect(replaceMock).toHaveBeenCalledWith("/dashboard");
  });

  it("shows safe error on failed login", async () => {
    const user = userEvent.setup();
    const { ApiError } = await import("@/lib/api/client");
    loginMock.mockRejectedValue(new ApiError(401, "Invalid email or password."));
    wrap(<LoginForm />);
    await user.type(screen.getByLabelText(/email/i), "owner@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "wrong");
    await user.click(screen.getByRole("button", { name: /sign in/i }));
    expect(await screen.findByText(/invalid email or password/i)).toBeInTheDocument();
  });

  it("toggles password visibility", async () => {
    const user = userEvent.setup();
    wrap(<LoginForm />);
    const password = screen.getByLabelText(/^password$/i);
    expect(password).toHaveAttribute("type", "password");
    await user.click(screen.getByRole("button", { name: /show password/i }));
    expect(password).toHaveAttribute("type", "text");
    await user.click(screen.getByRole("button", { name: /hide password/i }));
    expect(password).toHaveAttribute("type", "password");
  });
});

describe("tokenStore", () => {
  it("does not expose tokens through accidental logging helpers", () => {
    tokenStore.setAccessToken("secret-token");
    expect(tokenStore.getAccessToken()).toBe("secret-token");
    tokenStore.clear();
    expect(tokenStore.getAccessToken()).toBeNull();
  });
});

describe("Dashboard pieces", () => {
  it("renders metric card", () => {
    wrap(
      <MetricCard
        label="Projects"
        value={12}
        availability="live"
        icon={FolderKanban}
      />,
    );
    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
  });

  it("renders daily goal progress", () => {
    wrap(
      <DailyGoalCard
        goal={{
          label: "2 approved scripts per day",
          completed: 1,
          target: 2,
          remaining: 118,
          completionPercent: 1.6,
          weeklyCompleted: 0,
          weeklyTarget: 14,
          availability: "live",
        }}
      />,
    );
    expect(screen.getByText(/today'?s goal/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/50% of daily goal/i)).toBeInTheDocument();
    expect(screen.getByText(/1 \/ 2/)).toBeInTheDocument();
  });

  it("renders recent projects", () => {
    wrap(
      <RecentProjectsList
        projects={[
          {
            id: "1",
            projectCode: "CRX-0001",
            name: "Black Holes",
            category: "Science",
            status: "active",
            updatedAt: new Date().toISOString(),
          },
        ]}
      />,
    );
    expect(screen.getByText("Black Holes")).toBeInTheDocument();
    expect(screen.getByText("CRX-0001")).toBeInTheDocument();
  });

  it("renders recent scripts", () => {
    wrap(
      <RecentScriptsList
        scripts={[
          {
            id: "1",
            projectId: "p1",
            title: "Event Horizon",
            projectCode: "CRX-0001",
            status: "draft",
            updatedAt: new Date().toISOString(),
          },
        ]}
      />,
    );
    expect(screen.getByText("Event Horizon")).toBeInTheDocument();
  });

  it("renders pending reviews", () => {
    wrap(
      <PendingReviewsList
        reviews={[
          {
            id: "1",
            title: "Review me",
            versionNumber: 2,
            status: "pending",
            reviewerInitials: "PG",
            updatedAt: new Date().toISOString(),
          },
        ]}
      />,
    );
    expect(screen.getByText("Review me")).toBeInTheDocument();
    expect(screen.getByText(/v2/i)).toBeInTheDocument();
  });

  it("renders activity and empty/restricted states", () => {
    const { rerender } = wrap(
      <ActivityTimeline
        items={[
          {
            id: "1",
            action: "x",
            summary: "Story Spine updated",
            actorName: "You",
            createdAt: new Date().toISOString(),
          },
        ]}
      />,
    );
    expect(screen.getByText("Story Spine updated")).toBeInTheDocument();
    rerender(<ActivityTimeline items={[]} restricted />);
    expect(screen.getByText(/activity restricted/i)).toBeInTheDocument();
    wrap(<EmptyState title="No projects yet" />);
    expect(screen.getByText(/no projects yet/i)).toBeInTheDocument();
  });
});

describe("StatusBadge", () => {
  it("uses valid labels", () => {
    wrap(<StatusBadge status="in_review" />);
    expect(screen.getByText(statusLabel("in_review"))).toBeInTheDocument();
    wrap(<StatusBadge status="approved" />);
    expect(screen.getByText("Approved")).toBeInTheDocument();
  });
});

describe("SidebarNavigation", () => {
  it("renders primary navigation and marks active item", () => {
    wrap(<SidebarNavigation />);
    expect(screen.getByRole("link", { name: "Dashboard" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Session" })).toHaveAttribute(
      "href",
      "/production/session",
    );
    expect(screen.getByRole("link", { name: "Production" })).toHaveAttribute(
      "href",
      "/production",
    );
    expect(screen.getByRole("link", { name: "Projects" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Topics" })).toBeInTheDocument();
  });
});
