import { ReviewDetailPage } from "@/components/reviews/review-detail-page";

export const metadata = { title: "Review" };

type PageProps = {
  params: Promise<{ approvalId: string }>;
};

export default async function Page({ params }: PageProps) {
  const { approvalId } = await params;
  return <ReviewDetailPage approvalId={approvalId} />;
}
