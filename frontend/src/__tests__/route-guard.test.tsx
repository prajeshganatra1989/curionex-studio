import { describe, expect, it } from "vitest";

import { RequireAuth } from "@/components/auth/route-guards";
import { render } from "@testing-library/react";
import { vi } from "vitest";

const replaceMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock, push: vi.fn() }),
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
  it("redirects unauthenticated users to login", async () => {
    render(
      <RequireAuth>
        <div>Secret</div>
      </RequireAuth>,
    );
    expect(replaceMock).toHaveBeenCalledWith(
      expect.stringMatching(/^\/login\?next=/),
    );
  });
});
