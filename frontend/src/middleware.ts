import { NextResponse, type NextRequest } from "next/server";

import { AUTH_SESSION_COOKIE } from "@/lib/auth/constants";

const PUBLIC_PATHS = new Set(["/login"]);

export function middleware(request: NextRequest) {
  const host = request.headers.get("host") || "";

  // Canonicalize 127.0.0.1 → localhost so sessionStorage/cookies stay on one origin.
  if (host.startsWith("127.0.0.1")) {
    const url = request.nextUrl.clone();
    url.hostname = "localhost";
    return NextResponse.redirect(url);
  }

  const { pathname } = request.nextUrl;
  const hasSession = Boolean(
    request.cookies.get(AUTH_SESSION_COOKIE)?.value,
  );

  const isPublic = PUBLIC_PATHS.has(pathname);
  const isAsset =
    pathname.startsWith("/_next") ||
    pathname.startsWith("/brand") ||
    pathname.includes(".");

  if (isAsset) {
    return NextResponse.next();
  }

  // Only gate protected routes. Do NOT bounce /login → /dashboard from the
  // cookie alone — a stale cookie with no JWT caused an infinite loading loop.
  if (!hasSession && !isPublic && pathname !== "/login") {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
