import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ReviewsPage } from "@/components/reviews/reviews-page";
import { ReviewDetailPage } from "@/components/reviews/review-detail-page";
import { ToastProvider } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import type { ApprovalDetail, ApprovalListResponse } from "@/lib/api/types";

const pushMock = vi.fn();
const replaceMock = vi.fn();
const listApprovals = vi.fn();
const getApprovalDetail = vi.fn();
const approveApproval = vi.fn();
const rejectApproval = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: replaceMock }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/reviews",
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

vi.mock("@/lib/api/approvals", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/approvals")>(
    "@/lib/api/approvals",
  );
  return {
    ...actual,
    listApprovals: (...args: unknown[]) => listApprovals(...args),
    getApprovalDetail: (...args: unknown[]) => getApprovalDetail(...args),
    approveApproval: (...args: unknown[]) => approveApproval(...args),
    rejectApproval: (...args: unknown[]) => rejectApproval(...args),
  };
});

vi.mock("@/lib/auth/auth-context", () => ({
  useAuth: () => ({
    status: "authenticated",
    user: {
      id: "reviewer-1",
      email: "reviewer@example.com",
      first_name: "Pat",
      last_name: "Reviewer",
      is_active: true,
      created_at: "",
      updated_at: "",
    },
    login: vi.fn(),
    logout: vi.fn(),
    api: { baseUrl: "http://test" },
  }),
}));

const listResponse: ApprovalListResponse = {
  items: [
    {
      id: "ap-1",
      status: "pending",
      comment: null,
      created_at: "2026-01-03T00:00:00Z",
      reviewed_at: null,
      requested_by: {
        id: "u1",
        email: "owner@example.com",
        first_name: "Owner",
        last_name: "User",
      },
      reviewed_by: null,
      content_version: {
        id: "v1",
        project_id: "proj-1",
        script_id: "sc-1",
        version_number: 1,
        status: "in_review",
        title: "Snapshot",
        created_by: "u1",
        created_at: "2026-01-03T00:00:00Z",
      },
      project: {
        id: "proj-1",
        project_code: "CRX-0042",
        name: "Cosmic Mysteries",
      },
      script: {
        id: "sc-1",
        script_code: "CRX-0042-S01",
        title: "Neutron Stars",
        project_id: "proj-1",
        knowledge_pack_id: null,
      },
    },
  ],
  page: 1,
  page_size: 12,
  total: 1,
};

const detail: ApprovalDetail = {
  id: "ap-1",
  status: "pending",
  comment: null,
  created_at: "2026-01-03T00:00:00Z",
  reviewed_at: null,
  requested_by: listResponse.items[0]!.requested_by,
  reviewed_by: null,
  content_version: {
    id: "v1",
    project_id: "proj-1",
    script_id: "sc-1",
    version_number: 1,
    status: "in_review",
    title: "Snapshot",
    content: [
      "DISCOVERY BRIEF",
      "",
      "Brief",
      "",
      "STORY SPINE",
      "",
      "Spine",
      "",
      "MASTER SCRIPT",
      "",
      "Script",
      "",
    ].join("\n"),
    created_by: "u1",
    created_at: "2026-01-03T00:00:00Z",
  },
  project: listResponse.items[0]!.project,
  script: listResponse.items[0]!.script,
  version_approvals: [],
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

describe("Reviews UI", () => {
  beforeEach(() => {
    listApprovals.mockReset();
    getApprovalDetail.mockReset();
    approveApproval.mockReset();
    rejectApproval.mockReset();
    listApprovals.mockResolvedValue(listResponse);
    getApprovalDetail.mockResolvedValue(detail);
    approveApproval.mockResolvedValue({ id: "ap-1", status: "approved" });
    rejectApproval.mockResolvedValue({ id: "ap-1", status: "rejected" });
  });

  it("lists pending reviews", async () => {
    wrap(<ReviewsPage />);
    expect(await screen.findByTestId("reviews-list")).toBeInTheDocument();
    expect(screen.getByText("Neutron Stars")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Neutron Stars/i })).toHaveAttribute(
      "href",
      "/reviews/ap-1",
    );
  });

  it("shows restricted inbox on 403", async () => {
    listApprovals.mockRejectedValue(new ApiError(403, "Forbidden"));
    wrap(<ReviewsPage />);
    expect(await screen.findByText("Access restricted")).toBeInTheDocument();
  });

  it("renders review detail snapshot and approve action", async () => {
    const user = userEvent.setup();
    wrap(<ReviewDetailPage approvalId="ap-1" />);
    expect(await screen.findByRole("heading", { name: "Neutron Stars" })).toBeInTheDocument();
    expect(screen.getByTestId("snapshot-discovery_brief")).toHaveTextContent("Brief");
    await user.click(screen.getByRole("button", { name: "Approve" }));
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Confirm approve" }));
    expect(approveApproval).toHaveBeenCalled();
  });
});
