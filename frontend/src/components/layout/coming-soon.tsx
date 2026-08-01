import Link from "next/link";

import { PageContainer, PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/ui/empty-state";

type ComingSoonProps = {
  title: string;
  description: string;
};

export function ComingSoonPage({ title, description }: ComingSoonProps) {
  return (
    <PageContainer>
      <PageHeader title={title} description={description} />
      <EmptyState
        title="Coming in the next sprint"
        description="This module is intentionally a polished placeholder while we ship the foundation, login, and dashboard."
        action={
          <Link
            href="/dashboard"
            className="text-sm font-medium text-brand-orange hover:underline"
          >
            Back to dashboard
          </Link>
        }
      />
    </PageContainer>
  );
}
