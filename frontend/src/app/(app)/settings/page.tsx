import Link from "next/link";
import { Sparkles } from "lucide-react";

import { PageContainer, PageHeader } from "@/components/layout/page-header";

export const metadata = { title: "Settings" };

export default function SettingsPage() {
  return (
    <PageContainer>
      <PageHeader
        title="Settings"
        description="Studio preferences and configuration."
      />
      <Link
        href="/ai/settings"
        className="panel flex items-center gap-4 p-5 transition hover:border-brand-orange/40 hover:bg-surface-hover"
      >
        <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-brand-orange/10 text-brand-orange">
          <Sparkles className="h-5 w-5" aria-hidden />
        </span>
        <div>
          <h2 className="text-base font-semibold text-foreground">
            AI Foundation
          </h2>
          <p className="text-sm text-muted-foreground">
            Providers, models, credentials, and generation defaults.
          </p>
        </div>
      </Link>
    </PageContainer>
  );
}
