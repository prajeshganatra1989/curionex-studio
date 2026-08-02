import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

import { DashboardPage } from "@/components/dashboard/dashboard-page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => "/dashboard",
}));

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
    ...rest
  }: {
    children: React.ReactNode;
    href: string;
  } & Record<string, unknown>) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

vi.mock("@/lib/auth/auth-context", () => ({
  useAuth: () => ({
    status: "authenticated",
    user: {
      id: "1",
      email: "prajesh@example.com",
      first_name: "Prajesh",
      last_name: "Ganatra",
      is_active: true,
      created_at: "",
      updated_at: "",
    },
    login: vi.fn(),
    logout: vi.fn(),
    api: { baseUrl: "http://test" },
  }),
}));

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("only launches the Production Session", () => {
    render(<DashboardPage />);
    expect(screen.getByTestId("dashboard-session-launch")).toBeInTheDocument();
    const link = screen.getByTestId("open-production-session");
    expect(link).toHaveAttribute("href", "/production/session");
    expect(screen.getByText(/open production session/i)).toBeInTheDocument();
    expect(screen.queryByTestId("open-production-mode")).not.toBeInTheDocument();
  });
});
