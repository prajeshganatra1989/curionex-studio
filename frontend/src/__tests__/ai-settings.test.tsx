import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AiSettingsPage } from "@/components/ai/ai-settings-page";
import { ToastProvider } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import type { AiProvider, AiModel, AiSettings } from "@/lib/ai/types";

const listProviders = vi.fn();
const listModels = vi.fn();
const getAiSettings = vi.fn();
const setProviderCredentials = vi.fn();
const updateProvider = vi.fn();
const updateAiSettings = vi.fn();
const updateModel = vi.fn();

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
    listProviders: (...args: unknown[]) => listProviders(...args),
    listModels: (...args: unknown[]) => listModels(...args),
    getAiSettings: (...args: unknown[]) => getAiSettings(...args),
    setProviderCredentials: (...args: unknown[]) =>
      setProviderCredentials(...args),
    updateProvider: (...args: unknown[]) => updateProvider(...args),
    updateAiSettings: (...args: unknown[]) => updateAiSettings(...args),
    updateModel: (...args: unknown[]) => updateModel(...args),
  };
});

vi.mock("@/lib/auth/auth-context", () => ({
  useAuth: () => ({
    status: "authenticated",
    user: {
      id: "admin-1",
      email: "admin@example.com",
      first_name: "Admin",
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

const provider: AiProvider = {
  id: "prov-1",
  code: "openai",
  name: "OpenAI",
  is_active: true,
  base_url: "https://api.openai.com/v1",
  has_credentials: false,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const model: AiModel = {
  id: "model-1",
  provider_id: "prov-1",
  code: "gpt-4o",
  name: "GPT-4o",
  context_window: 128000,
  supports_reasoning: false,
  supports_streaming: true,
  is_active: true,
  is_default: true,
  pricing_input_per_1k: 0.005,
  pricing_output_per_1k: 0.015,
};

const settings: AiSettings = {
  default_model_id: "model-1",
  default_temperature: 0.7,
  default_max_tokens: 4096,
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

describe("AI Settings UI", () => {
  beforeEach(() => {
    listProviders.mockReset();
    listModels.mockReset();
    getAiSettings.mockReset();
    setProviderCredentials.mockReset();
    updateProvider.mockReset();
    updateAiSettings.mockReset();
    updateModel.mockReset();
    listProviders.mockResolvedValue([provider]);
    listModels.mockResolvedValue([model]);
    getAiSettings.mockResolvedValue(settings);
    setProviderCredentials.mockResolvedValue({
      ...provider,
      has_credentials: true,
    });
  });

  it("shows credential status without exposing stored keys", async () => {
    wrap(<AiSettingsPage />);
    expect(await screen.findByText("Not configured")).toBeInTheDocument();
    expect(screen.queryByDisplayValue("sk-secret")).not.toBeInTheDocument();
    const keyInput = screen.getByTestId("api-key-input-openai");
    expect(keyInput).toHaveAttribute("type", "password");
  });

  it("submits masked api key without displaying it after save", async () => {
    const user = userEvent.setup();
    wrap(<AiSettingsPage />);
    const keyInput = await screen.findByTestId("api-key-input-openai");
    await user.type(keyInput, "sk-test-key-12345");
    await user.click(screen.getByRole("button", { name: "Save key" }));
    expect(setProviderCredentials).toHaveBeenCalledWith(
      expect.anything(),
      "prov-1",
      { api_key: "sk-test-key-12345" },
    );
    expect(screen.queryByDisplayValue("sk-test-key-12345")).not.toBeInTheDocument();
  });

  it("shows restricted settings on 403", async () => {
    listProviders.mockRejectedValue(new ApiError(403, "Forbidden"));
    getAiSettings.mockRejectedValue(new ApiError(403, "Forbidden"));
    listModels.mockRejectedValue(new ApiError(403, "Forbidden"));
    wrap(<AiSettingsPage />);
    expect(await screen.findByText("Access restricted")).toBeInTheDocument();
  });
});
