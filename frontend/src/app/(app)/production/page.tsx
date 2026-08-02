import { Suspense } from "react";

import { ProductionPage } from "@/components/production/production-page";
import { PageContainer } from "@/components/layout/page-header";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";

export const metadata = {
  title: "Production Mode",
};

function ProductionFallback() {
  return (
    <PageContainer>
      <LoadingSkeleton className="mb-4 h-16" />
      <LoadingSkeleton className="mb-4 h-48" />
      <LoadingSkeleton className="h-64" />
    </PageContainer>
  );
}

export default function ProductionRoute() {
  return (
    <Suspense fallback={<ProductionFallback />}>
      <ProductionPage />
    </Suspense>
  );
}
