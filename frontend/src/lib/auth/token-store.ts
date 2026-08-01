/**
 * Token storage abstraction.
 *
 * The backend currently returns a Bearer JWT from POST /auth/login and does not
 * set HttpOnly cookies. Until cookie-based sessions are available, tokens are
 * kept in sessionStorage through this module only.
 *
 * Security tradeoff: sessionStorage is still readable by XSS. Prefer migrating
 * to HttpOnly Secure cookies when the API supports them. Never log tokens or
 * put them in URLs.
 */

import {
  ACCESS_TOKEN_STORAGE_KEY,
  AUTH_SESSION_COOKIE,
} from "@/lib/auth/constants";

function canUseDom(): boolean {
  return typeof window !== "undefined";
}

export const tokenStore = {
  getAccessToken(): string | null {
    if (!canUseDom()) return null;
    return window.sessionStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
  },

  setAccessToken(token: string): void {
    if (!canUseDom()) return;
    window.sessionStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, token);
    // Non-secret presence flag for middleware redirects (not the JWT).
    document.cookie = `${AUTH_SESSION_COOKIE}=1; path=/; SameSite=Lax`;
  },

  clear(): void {
    if (!canUseDom()) return;
    window.sessionStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
    document.cookie = `${AUTH_SESSION_COOKIE}=; path=/; Max-Age=0; SameSite=Lax`;
  },

  hasSessionCookie(): boolean {
    if (!canUseDom()) return false;
    return document.cookie
      .split(";")
      .some((part) => part.trim().startsWith(`${AUTH_SESSION_COOKIE}=`));
  },
};
