import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { DashboardPage } from "@/components/dashboard/dashboard-page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => "/dashboard",
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
    api: {},
  }),
}));

describe("DashboardPage", () => {
  it("shows greeting with authenticated first name and panels", async () => {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={client}>
        <DashboardPage />
      </QueryClientProvider>,
    );
    expect(await screen.findByText(/Prajesh/)).toBeInTheDocument();
    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Recent Projects" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Recent Scripts" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Pending Reviews" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Recent Activity" })).toBeInTheDocument();
  });
});
