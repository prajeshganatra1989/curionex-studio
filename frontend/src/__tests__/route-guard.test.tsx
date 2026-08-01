import { afterEach, describe, expect, it, vi } from "vitest";
import { render, waitFor } from "@testing-library/react";

import { RequireAuth } from "@/components/auth/route-guards";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => "/dashboard",
}));

vi.mock("@/lib/auth/auth-context", () => ({
  useAuth: () => ({
    status: "unauthenticated",
    user: null,
    login: vi.fn(),
    logout: vi.fn(),
    api: {},
  }),
}));

describe("RequireAuth", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("redirects unauthenticated users to login", async () => {
    const replace = vi.fn();
    vi.stubGlobal("location", { replace });

    render(
      <RequireAuth>
        <div>Secret</div>
      </RequireAuth>,
    );

    await waitFor(() => {
      expect(replace).toHaveBeenCalledWith(
        expect.stringMatching(/^\/login\?next=/),
      );
    });
  });
});
