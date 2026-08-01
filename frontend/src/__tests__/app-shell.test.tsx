import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AppShell } from "@/components/layout/app-shell";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => "/dashboard",
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("next/image", () => ({
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

vi.mock("@/lib/auth/auth-context", () => ({
  useAuth: () => ({
    status: "authenticated",
    user: {
      id: "1",
      email: "prajesh@example.com",
      first_name: "Prajesh",
      last_name: "G",
      is_active: true,
      created_at: "",
      updated_at: "",
    },
    login: vi.fn(),
    logout: vi.fn(),
    api: {},
  }),
}));

describe("AppShell mobile navigation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("can open and close the mobile drawer", async () => {
    const user = userEvent.setup();
    render(
      <AppShell>
        <div>Content</div>
      </AppShell>,
    );
    expect(screen.getByText("Content")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /open menu/i }));
    expect(
      screen.getByRole("button", { name: /close navigation/i }),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /close navigation/i }));
    expect(
      screen.queryByRole("button", { name: /close navigation/i }),
    ).not.toBeInTheDocument();
  });
});
