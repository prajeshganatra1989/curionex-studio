import type { ApiClient } from "@/lib/api/client";

export type User = {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export function loginRequest(client: ApiClient, payload: LoginPayload) {
  return client.post<TokenResponse>("/auth/login", payload);
}

export function fetchCurrentUser(client: ApiClient) {
  return client.get<User>("/auth/me");
}
