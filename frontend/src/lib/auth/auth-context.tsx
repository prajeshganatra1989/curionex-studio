"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { fetchCurrentUser, loginRequest, type User } from "@/lib/api/auth";
import { ApiError, createApiClient } from "@/lib/api/client";
import { tokenStore } from "@/lib/auth/token-store";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

type AuthContextValue = {
  status: AuthStatus;
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  api: ReturnType<typeof createApiClient>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<User | null>(null);

  const handleUnauthorized = useCallback(() => {
    tokenStore.clear();
    setUser(null);
    setStatus("unauthenticated");
  }, []);

  const api = useMemo(
    () =>
      createApiClient({
        getToken: () => tokenStore.getAccessToken(),
        onUnauthorized: handleUnauthorized,
      }),
    [handleUnauthorized],
  );

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      const token = tokenStore.getAccessToken();
      if (!token) {
        if (!cancelled) {
          // Drop stale middleware cookie so /login is reachable.
          tokenStore.clear();
          setStatus("unauthenticated");
          setUser(null);
        }
        return;
      }

      try {
        const me = await fetchCurrentUser(api);
        if (!cancelled) {
          setUser(me);
          setStatus("authenticated");
        }
      } catch (error) {
        if (!cancelled) {
          tokenStore.clear();
          setUser(null);
          setStatus("unauthenticated");
          if (!(error instanceof ApiError && error.status === 401)) {
            // Keep unauthenticated; login page can show connectivity issues.
          }
        }
      }
    }

    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, [api]);

  const login = useCallback(
    async (email: string, password: string) => {
      const token = await loginRequest(api, { email, password });
      tokenStore.setAccessToken(token.access_token);
      const me = await fetchCurrentUser(api);
      setUser(me);
      setStatus("authenticated");
    },
    [api],
  );

  const logout = useCallback(() => {
    tokenStore.clear();
    setUser(null);
    setStatus("unauthenticated");
  }, []);

  const value = useMemo(
    () => ({ status, user, login, logout, api }),
    [status, user, login, logout, api],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
