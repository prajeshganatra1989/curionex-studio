import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { JobsPage } from "@/components/ai/jobs-page";
import { ToastProvider } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import type { AiJob, PaginatedResponse } from "@/lib/ai/types";

const replaceMock = vi.fn();
const listJobs = vi.fn();
const cancelJob = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: replaceMock }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/ai/jobs",
}));

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

vi.mock("@/lib/api/ai", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/ai")>(
    "@/lib/api/ai",
  );
  return {
    ...actual,
    listJobs: (...args: unknown[]) => listJobs(...args),
    cancelJob: (...args: unknown[]) => cancelJob(...args),
  };
});

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

const job: AiJob = {
  id: "job-abc-123",
  status: "queued",
  requested_by: "user-1",
  prompt_version_id: "ver-1",
  model_id: "model-1",
  input_variables: { topic: "Neutron stars" },
  started_at: null,
  finished_at: null,
  duration_ms: null,
  retries: 0,
  error_message: null,
  created_at: "2026-01-03T00:00:00Z",
};

const listResponse: PaginatedResponse<AiJob> = {
  items: [job],
  page: 1,
  page_size: 12,
  total: 1,
};

function wrap(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <ToastProvider>{ui}</ToastProvider>
    </QueryClientProvider>,
  );
}

describe("AI Jobs UI", () => {
  beforeEach(() => {
    listJobs.mockReset();
    cancelJob.mockReset();
    listJobs.mockResolvedValue(listResponse);
    cancelJob.mockResolvedValue({ ...job, status: "cancelled" });
  });

  it("lists jobs with status badges", async () => {
    wrap(<JobsPage />);
    expect(await screen.findByTestId("jobs-list")).toBeInTheDocument();
    expect(screen.getByText("job-abc-123")).toBeInTheDocument();
    expect(screen.getByTestId("jobs-list")).toHaveTextContent("Queued");
  });

  it("cancels a queued job", async () => {
    const user = userEvent.setup();
    wrap(<JobsPage />);
    await screen.findByTestId("jobs-list");
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(cancelJob).toHaveBeenCalledWith(expect.anything(), "job-abc-123");
  });

  it("shows restricted jobs on 403", async () => {
    listJobs.mockRejectedValue(new ApiError(403, "Forbidden"));
    wrap(<JobsPage />);
    expect(await screen.findByText("Access restricted")).toBeInTheDocument();
  });
});
