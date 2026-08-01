import { Suspense } from "react";

import { ProjectsPage } from "@/components/projects/projects-page";
import { PageContainer } from "@/components/layout/page-header";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";

export const metadata = { title: "Projects" };

function ProjectsFallback() {
  return (
    <PageContainer>
      <LoadingSkeleton className="mb-4 h-16" />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <LoadingSkeleton key={i} className="h-44" />
        ))}
      </div>
    </PageContainer>
  );
}

export default function ProjectsRoutePage() {
  return (
    <Suspense fallback={<ProjectsFallback />}>
      <ProjectsPage />
    </Suspense>
  );
}
