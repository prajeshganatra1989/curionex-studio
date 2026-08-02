export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;
  /** Raw JSON `detail` payload when it is not a plain string (e.g. structured conflict errors). */
  readonly data?: unknown;

  constructor(status: number, detail: string, data?: unknown) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.data = data;
  }
}

export type ApiClientOptions = {
  baseUrl?: string;
  getToken?: () => string | null;
  onUnauthorized?: () => void;
};

function resolveBaseUrl(explicit?: string): string {
  if (explicit) return explicit.replace(/\/$/, "");
  const fromEnv = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (fromEnv) return fromEnv.replace(/\/$/, "");
  return "http://127.0.0.1:8000";
}

async function parseError(response: Response): Promise<ApiError> {
  let detail = `Request failed (${response.status})`;
  let data: unknown;
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") {
      detail = body.detail;
    } else if (Array.isArray(body.detail)) {
      detail = body.detail
        .map((item) => {
          if (typeof item === "string") return item;
          if (item && typeof item === "object" && "msg" in item) {
            return String((item as { msg: unknown }).msg);
          }
          return JSON.stringify(item);
        })
        .join("; ");
    } else if (body.detail && typeof body.detail === "object") {
      // Structured detail (e.g. { message, conflicts } on 409 conflict responses).
      data = body.detail;
      const message = (body.detail as { message?: unknown }).message;
      if (typeof message === "string") detail = message;
    }
  } catch {
    // Keep default detail.
  }
  return new ApiError(response.status, detail, data);
}

export function createApiClient(options: ApiClientOptions = {}) {
  const baseUrl = resolveBaseUrl(options.baseUrl);

  async function request<T>(
    path: string,
    init: RequestInit = {},
  ): Promise<T> {
    const headers = new Headers(init.headers);
    if (!headers.has("Content-Type") && init.body) {
      headers.set("Content-Type", "application/json");
    }

    const token = options.getToken?.() ?? null;
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(`${baseUrl}${path}`, {
      ...init,
      headers,
    });

    if (response.status === 401) {
      options.onUnauthorized?.();
      throw await parseError(response);
    }

    if (!response.ok) {
      throw await parseError(response);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return (await response.json()) as T;
  }

  return {
    baseUrl,
    request,
    get: <T>(path: string) => request<T>(path, { method: "GET" }),
    post: <T>(path: string, body?: unknown) =>
      request<T>(path, {
        method: "POST",
        body: body === undefined ? undefined : JSON.stringify(body),
      }),
    patch: <T>(path: string, body?: unknown) =>
      request<T>(path, {
        method: "PATCH",
        body: body === undefined ? undefined : JSON.stringify(body),
      }),
    delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
    put: <T>(path: string, body?: unknown) =>
      request<T>(path, {
        method: "PUT",
        body: body === undefined ? undefined : JSON.stringify(body),
      }),
  };
}

export type ApiClient = ReturnType<typeof createApiClient>;
