import { Suspense } from "react";

import { TopicsPage } from "@/components/editorial/topics-page";
import { PageContainer } from "@/components/layout/page-header";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";

export const metadata = { title: "Editorial Library" };

function TopicsFallback() {
  return (
    <PageContainer>
      <LoadingSkeleton className="mb-4 h-16" />
      <LoadingSkeleton className="h-64" />
    </PageContainer>
  );
}

export default function TopicsRoutePage() {
  return (
    <Suspense fallback={<TopicsFallback />}>
      <TopicsPage />
    </Suspense>
  );
}
