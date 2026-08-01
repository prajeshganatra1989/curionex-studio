import { RequireAuth } from "@/components/auth/route-guards";
import { AppShell } from "@/components/layout/app-shell";

export default function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RequireAuth>
      <AppShell>{children}</AppShell>
    </RequireAuth>
  );
}
