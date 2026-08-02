"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowLeft } from "lucide-react";

import { KnowledgePackContextPanel } from "@/components/scripts/knowledge-pack-context-panel";
import { PageContainer } from "@/components/layout/page-header";
import { AvatarInitials } from "@/components/ui/avatar-initials";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Field, TextArea } from "@/components/ui/field";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { Modal } from "@/components/ui/modal";
import { StatusBadge } from "@/components/ui/status-badge";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import {
  useApproval,
  useApproveApproval,
  useCancelApproval,
  useRejectApproval,
} from "@/lib/reviews/hooks";
import { parseSnapshot } from "@/lib/scripts/snapshot";
import { formatRelativeTime } from "@/lib/utils";
import { useAuth } from "@/lib/auth/auth-context";

type ReviewDetailPageProps = {
  approvalId: string;
};

export function ReviewDetailPage({ approvalId }: ReviewDetailPageProps) {
  const router = useRouter();
  const { toast } = useToast();
  const { user } = useAuth();
  const approvalQuery = useApproval(approvalId);
  const approveMutation = useApproveApproval(
    approvalId,
    approvalQuery.data?.script?.id,
  );
  const rejectMutation = useRejectApproval(
    approvalId,
    approvalQuery.data?.script?.id,
  );
  const cancelMutation = useCancelApproval(
    approvalId,
    approvalQuery.data?.script?.id,
  );

  const [approveOpen, setApproveOpen] = useState(false);
  const [rejectOpen, setRejectOpen] = useState(false);
  const [cancelOpen, setCancelOpen] = useState(false);
  const [approveComment, setApproveComment] = useState("");
  const [rejectComment, setRejectComment] = useState("");
  const [cancelComment, setCancelComment] = useState("");

  const data = approvalQuery.data;
  const snapshot = data ? parseSnapshot(data.content_version.content) : null;
  const isPending = data?.status === "pending";
  const isRequester = user?.id === data?.requested_by.id;

  async function runApprove() {
    try {
      await approveMutation.mutateAsync({
        comment: approveComment.trim() || null,
      });
      setApproveOpen(false);
      toast({ title: "Approval recorded", tone: "success" });
    } catch (err) {
      toast({
        title: "Could not approve",
        description: err instanceof ApiError ? err.detail : "Try again.",
        tone: "error",
      });
    }
  }

  async function runReject() {
    const comment = rejectComment.trim();
    if (!comment) {
      toast({
        title: "Comment required",
        description: "Explain what needs to change before rejecting.",
        tone: "error",
      });
      return;
    }
    try {
      await rejectMutation.mutateAsync({ comment });
      setRejectOpen(false);
      toast({ title: "Revisions requested", tone: "success" });
    } catch (err) {
      toast({
        title: "Could not reject",
        description: err instanceof ApiError ? err.detail : "Try again.",
        tone: "error",
      });
    }
  }

  async function runCancel() {
    try {
      await cancelMutation.mutateAsync({
        comment: cancelComment.trim() || null,
      });
      setCancelOpen(false);
      toast({ title: "Review cancelled", tone: "success" });
    } catch (err) {
      toast({
        title: "Could not cancel",
        description: err instanceof ApiError ? err.detail : "Try again.",
        tone: "error",
      });
    }
  }

  if (approvalQuery.isLoading) {
    return (
      <PageContainer>
        <LoadingSkeleton className="mb-4 h-10 w-48" />
        <LoadingSkeleton className="mb-6 h-32" />
        <LoadingSkeleton className="h-96" />
      </PageContainer>
    );
  }

  if (approvalQuery.isError || !data) {
    const status =
      approvalQuery.error instanceof ApiError
        ? approvalQuery.error.status
        : 0;
    if (status === 404) {
      return (
        <PageContainer>
          <EmptyState
            title="Review not found"
            description="It may have been removed or you may not have access."
            action={
              <Link href="/reviews" className="text-sm text-brand-orange underline">
                Back to Reviews
              </Link>
            }
          />
        </PageContainer>
      );
    }
    if (status === 403) {
      return (
        <PageContainer>
          <EmptyState
            title="Access restricted"
            description="You do not have permission to view this review."
          />
        </PageContainer>
      );
    }
    return (
      <PageContainer>
        <ErrorState
          message={
            approvalQuery.error instanceof ApiError
              ? approvalQuery.error.detail
              : "Unable to load review."
          }
          action={
            <button
              type="button"
              className="text-sm text-brand-orange underline"
              onClick={() => void approvalQuery.refetch()}
            >
              Try again
            </button>
          }
        />
      </PageContainer>
    );
  }

  const title = data.script?.title ?? data.content_version.title;
  const workspaceHref =
    data.script && data.project
      ? `/projects/${data.project.id}/scripts/${data.script.id}`
      : null;
  const versionHref =
    data.script && data.project
      ? `/projects/${data.project.id}/scripts/${data.script.id}/versions/${data.content_version.id}`
      : null;

  return (
    <PageContainer>
      <div className="mb-6">
        <Link
          href="/reviews"
          className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Reviews
        </Link>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
                {title}
              </h1>
              <StatusBadge status={data.status} />
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              {data.project.project_code}
              {data.script ? (
                <>
                  <span aria-hidden> · </span>
                  {data.script.script_code}
                </>
              ) : null}
              <span aria-hidden> · </span>
              Version {data.content_version.version_number}
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
              <span className="inline-flex items-center gap-2">
                <AvatarInitials
                  name={`${data.requested_by.first_name} ${data.requested_by.last_name}`}
                />
                Requested by {data.requested_by.first_name}{" "}
                {data.requested_by.last_name}
              </span>
              <time dateTime={data.created_at}>
                {formatRelativeTime(data.created_at)}
              </time>
              {data.reviewed_by ? (
                <span>
                  Reviewed by {data.reviewed_by.first_name}{" "}
                  {data.reviewed_by.last_name}
                </span>
              ) : null}
            </div>
            {data.comment ? (
              <blockquote
                className="mt-3 rounded-lg border border-border bg-surface/60 px-3 py-2 text-sm"
                data-testid="review-comment"
              >
                {data.comment}
              </blockquote>
            ) : null}
          </div>
          <div className="flex flex-wrap gap-2">
            {workspaceHref ? (
              <Link
                href={workspaceHref}
                className="inline-flex h-10 items-center justify-center rounded-lg border border-border bg-surface-elevated px-4 text-sm text-foreground hover:bg-surface-hover"
              >
                Open Workspace
              </Link>
            ) : null}
            {versionHref ? (
              <Link
                href={versionHref}
                className="inline-flex h-10 items-center justify-center rounded-lg border border-border bg-surface-elevated px-4 text-sm text-foreground hover:bg-surface-hover"
              >
                Open Version
              </Link>
            ) : null}
            {isPending ? (
              <>
                <Button type="button" onClick={() => setApproveOpen(true)}>
                  Approve
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setRejectOpen(true)}
                >
                  Reject
                </Button>
                {isRequester ? (
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => setCancelOpen(true)}
                  >
                    Cancel request
                  </Button>
                ) : null}
              </>
            ) : null}
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_17rem]">
        <div className="space-y-6">
          {snapshot?.sections.map((section) => (
            <section
              key={section.key}
              className="rounded-xl border border-border/70 bg-surface/40 p-4"
              data-testid={`snapshot-${section.key}`}
            >
              <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                {section.title}
              </h2>
              <pre className="mt-3 whitespace-pre-wrap text-sm text-foreground">
                {section.content.trim() || "—"}
              </pre>
            </section>
          ))}

          {data.version_approvals.length > 0 ? (
            <section className="rounded-xl border border-border/70 bg-surface/40 p-4">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                Approval history
              </h2>
              <ul className="mt-3 space-y-2 text-sm">
                {data.version_approvals.map((record) => (
                  <li
                    key={record.id}
                    className="rounded-lg border border-border/60 px-3 py-2"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge status={record.status} />
                      <time
                        className="text-xs text-muted-foreground"
                        dateTime={record.created_at}
                      >
                        {formatRelativeTime(record.created_at)}
                      </time>
                    </div>
                    {record.comment ? (
                      <p className="mt-1 text-xs text-muted-foreground">
                        {record.comment}
                      </p>
                    ) : null}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
        </div>

        {data.script?.knowledge_pack_id ? (
          <KnowledgePackContextPanel
            projectId={data.project.id}
            knowledgePackId={data.script.knowledge_pack_id}
            onAssociate={() => {
              if (workspaceHref) router.push(workspaceHref);
            }}
          />
        ) : null}
      </div>

      <Modal
        open={approveOpen}
        onClose={() => setApproveOpen(false)}
        title="Approve version"
        description="Optional note for the requester."
      >
        <Field label="Comment (optional)" htmlFor="approve-comment">
          <TextArea
            id="approve-comment"
            value={approveComment}
            onChange={(event) => setApproveComment(event.target.value)}
            rows={3}
          />
        </Field>
        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={() => setApproveOpen(false)}>
            Back
          </Button>
          <Button
            type="button"
            loading={approveMutation.isPending}
            onClick={() => void runApprove()}
          >
            Confirm approve
          </Button>
        </div>
      </Modal>

      <Modal
        open={rejectOpen}
        onClose={() => setRejectOpen(false)}
        title="Request revisions"
        description="A comment is required so the writer knows what to change."
      >
        <Field label="Comment" htmlFor="reject-comment">
          <TextArea
            id="reject-comment"
            value={rejectComment}
            onChange={(event) => setRejectComment(event.target.value)}
            rows={4}
            required
          />
        </Field>
        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={() => setRejectOpen(false)}>
            Back
          </Button>
          <Button
            type="button"
            variant="secondary"
            loading={rejectMutation.isPending}
            onClick={() => void runReject()}
          >
            Confirm reject
          </Button>
        </div>
      </Modal>

      <Modal
        open={cancelOpen}
        onClose={() => setCancelOpen(false)}
        title="Cancel review request"
        description="Withdraw this approval request while it is still pending."
      >
        <Field label="Comment (optional)" htmlFor="cancel-comment">
          <TextArea
            id="cancel-comment"
            value={cancelComment}
            onChange={(event) => setCancelComment(event.target.value)}
            rows={3}
          />
        </Field>
        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={() => setCancelOpen(false)}>
            Back
          </Button>
          <Button
            type="button"
            variant="ghost"
            loading={cancelMutation.isPending}
            onClick={() => void runCancel()}
          >
            Confirm cancel
          </Button>
        </div>
      </Modal>
    </PageContainer>
  );
}
