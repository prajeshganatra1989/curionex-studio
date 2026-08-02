"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import { ArrowLeft, Check, Clapperboard, Copy, Download, Loader2, RefreshCw } from "lucide-react";

import { PageContainer } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { ApiError } from "@/lib/api/client";
import type {
  ProductionPackage,
  ProductionPackageStoryboardV2Scene,
} from "@/lib/api/types";
import {
  useCreateProductionPackage,
  useProductionPackage,
  useProductionPackageEligibility,
  useScript,
} from "@/lib/scripts/hooks";

const TABS = [
  "overview",
  "storyboard",
  "storyboard_v2",
  "shot_list",
  "assets",
  "voice",
  "subtitles",
  "youtube",
  "qa",
] as const;

type TabId = (typeof TABS)[number];

const TAB_LABELS: Record<TabId, string> = {
  overview: "Overview",
  storyboard: "Storyboard",
  storyboard_v2: "Storyboard V2",
  shot_list: "Shot List",
  assets: "Assets",
  voice: "Voice",
  subtitles: "Subtitles",
  youtube: "YouTube",
  qa: "QA",
};

function PreBlock({ text }: { text: string }) {
  if (!text.trim()) {
    return <p className="text-sm text-muted-foreground">Empty</p>;
  }
  return (
    <pre className="max-h-80 overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-surface/60 p-3 text-xs text-foreground">
      {text}
    </pre>
  );
}

function OverviewTab({ pkg }: { pkg: ProductionPackage }) {
  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold text-foreground">Project</h2>
        <p className="mt-2 font-mono text-xs text-brand-amber">
          {pkg.project.project_code}
        </p>
        <p className="text-sm text-foreground">{pkg.project.name}</p>
        <p className="mt-1 text-xs text-muted-foreground">
          {pkg.project.description || "No description"}
        </p>
      </section>
      <section className="rounded-xl border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold text-foreground">Script</h2>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <span className="font-mono text-xs text-muted-foreground">
            {pkg.script.script_code}
          </span>
          <StatusBadge status={pkg.script.status} />
        </div>
        <p className="mt-1 text-sm font-medium">{pkg.script.title}</p>
      </section>
      <section className="rounded-xl border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold text-foreground">
          Knowledge Pack Summary
        </h2>
        <p className="mt-2 text-sm">
          {pkg.knowledge_pack.name ?? "No linked Knowledge Pack"}
        </p>
        {pkg.knowledge_pack.content_angle ? (
          <p className="mt-2 text-xs text-muted-foreground">
            {pkg.knowledge_pack.content_angle.slice(0, 400)}
          </p>
        ) : null}
      </section>
      <section className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-xl border border-border bg-surface p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Discovery Brief
          </h3>
          <div className="mt-2">
            <PreBlock text={pkg.discovery_brief} />
          </div>
        </div>
        <div className="rounded-xl border border-border bg-surface p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Story Spine
          </h3>
          <div className="mt-2">
            <PreBlock text={pkg.story_spine} />
          </div>
        </div>
        <div className="rounded-xl border border-border bg-surface p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Master Script
          </h3>
          <div className="mt-2">
            <PreBlock text={pkg.master_script} />
          </div>
        </div>
      </section>
      <section className="rounded-xl border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold">Quality Review Summary</h2>
        {pkg.quality_review.available ? (
          <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
            <li>Score: {pkg.quality_review.overall_score ?? "—"}</li>
            <li>Band: {pkg.quality_review.quality_band ?? "—"}</li>
            <li>
              Next: {pkg.quality_review.recommended_next_action ?? "—"}
            </li>
            <li>
              Gold threshold:{" "}
              {pkg.quality_review.gold_threshold_met ? "Met" : "Not met"}
            </li>
          </ul>
        ) : (
          <p className="mt-2 text-sm text-muted-foreground">
            No quality review attached.
          </p>
        )}
      </section>
      <section className="rounded-xl border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold">Production Metadata</h2>
        <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
          <li>Gold gate: {pkg.production_metadata.gold_gate}</li>
          <li>
            Target: {pkg.production_metadata.target_duration_seconds}s @{" "}
            {pkg.production_metadata.recommended_wpm} WPM
          </li>
          <li>Format: {pkg.production_metadata.format}</li>
          <li>{pkg.production_metadata.notes}</li>
        </ul>
      </section>
    </div>
  );
}

function StoryboardTab({ pkg }: { pkg: ProductionPackage }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-border">
      <table className="w-full min-w-[960px] text-left text-sm">
        <thead className="border-b border-border bg-surface-elevated text-xs uppercase tracking-wide text-muted-foreground">
          <tr>
            <th className="px-3 py-2">#</th>
            <th className="px-3 py-2">Time</th>
            <th className="px-3 py-2">Purpose</th>
            <th className="px-3 py-2">Narration</th>
            <th className="px-3 py-2">Visual</th>
            <th className="px-3 py-2">Motion</th>
            <th className="px-3 py-2">On-screen</th>
            <th className="px-3 py-2">Transition</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border bg-surface">
          {pkg.storyboard.map((scene) => (
            <tr key={scene.scene_number} className="align-top">
              <td className="px-3 py-3 tabular-nums">{scene.scene_number}</td>
              <td className="px-3 py-3 font-mono text-xs">{scene.time_range}</td>
              <td className="px-3 py-3 capitalize">
                {scene.purpose.replaceAll("_", " ")}
              </td>
              <td className="max-w-xs px-3 py-3 text-muted-foreground">
                {scene.narration}
              </td>
              <td className="max-w-[12rem] px-3 py-3 text-xs text-muted-foreground">
                {scene.suggested_visual}
              </td>
              <td className="max-w-[10rem] px-3 py-3 text-xs text-muted-foreground">
                {scene.suggested_motion}
              </td>
              <td className="max-w-[8rem] px-3 py-3 text-xs">
                {scene.suggested_on_screen_text}
              </td>
              <td className="px-3 py-3 text-xs text-muted-foreground">
                {scene.transition}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatSeconds(value: number): string {
  const whole = Math.max(0, Math.floor(value));
  const mins = Math.floor(whole / 60);
  const secs = whole % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

export function storyboardV2ToMarkdown(
  scenes: ProductionPackageStoryboardV2Scene[],
  title = "Production Storyboard V2",
): string {
  const lines = [`# ${title}`, ""];
  for (const scene of scenes) {
    lines.push(`## Scene ${scene.scene_number}`, "");
    lines.push(
      `- **Time:** ${scene.start_time.toFixed(2)}s – ${scene.end_time.toFixed(2)}s (${scene.duration.toFixed(2)}s)`,
    );
    lines.push(`- **Scene goal:** ${scene.scene_goal}`);
    lines.push(`- **Viewer emotion:** ${scene.viewer_emotion}`);
    lines.push(`- **Visual type:** ${scene.visual_type}`);
    lines.push(`- **Camera:** ${scene.camera_movement}`);
    lines.push(`- **Transition:** ${scene.transition}`);
    lines.push(`- **Animation:** ${scene.animation_suggestion}`);
    lines.push(`- **On-screen text:** ${scene.on_screen_text || "—"}`);
    lines.push(`- **Text position:** ${scene.text_position}`);
    lines.push(`- **Asset required:** ${scene.asset_required}`);
    lines.push(`- **Music mood:** ${scene.music_mood}`);
    lines.push(`- **SFX:** ${scene.sound_effects}`);
    lines.push(`- **Notes:** ${scene.notes}`, "");
    lines.push("**Narration**", "", scene.narration, "");
  }
  return `${lines.join("\n").trimEnd()}\n`;
}

function StoryboardV2Tab({ pkg }: { pkg: ProductionPackage }) {
  const [copied, setCopied] = useState(false);
  const scenes = useMemo(
    () => pkg.storyboard_v2 ?? [],
    [pkg.storyboard_v2],
  );
  const totalDuration = scenes.reduce((sum, s) => sum + s.duration, 0);
  const markdown = useMemo(
    () =>
      storyboardV2ToMarkdown(
        scenes,
        `${pkg.script.script_code} — Storyboard V2`,
      ),
    [pkg.script.script_code, scenes],
  );

  async function copyMarkdown() {
    try {
      await navigator.clipboard.writeText(markdown);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard may be unavailable in tests */
    }
  }

  function downloadMarkdown() {
    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${pkg.script.script_code}-storyboard-v2.md`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  if (!scenes.length) {
    return (
      <EmptyState
        title="No Storyboard V2 scenes"
        description="Regenerate the production package to build scene cards."
      />
    );
  }

  return (
    <div className="space-y-4" data-testid="storyboard-v2-panel">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">
          {scenes.length} scenes · ~{totalDuration.toFixed(1)}s timeline
        </p>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="secondary"
            onClick={() => void copyMarkdown()}
            data-testid="copy-storyboard-v2-markdown"
            className="h-9 px-3 text-xs"
          >
            {copied ? (
              <>
                <Check className="h-4 w-4" />
                Copied
              </>
            ) : (
              <>
                <Copy className="h-4 w-4" />
                Copy Markdown
              </>
            )}
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={downloadMarkdown}
            data-testid="export-storyboard-v2-markdown"
            className="h-9 px-3 text-xs"
          >
            <Download className="h-4 w-4" />
            Export Markdown
          </Button>
        </div>
      </div>

      <div
        className="relative overflow-x-auto pb-2"
        aria-label="Storyboard V2 timeline"
      >
        <div className="mb-3 flex min-w-[640px] gap-1">
          {scenes.map((scene) => {
            const flex = Math.max(scene.duration, 1);
            return (
              <div
                key={`rail-${scene.scene_number}`}
                className="rounded-md bg-brand-orange/20 px-2 py-1.5 text-center"
                style={{ flexGrow: flex, flexBasis: 0 }}
                title={`Scene ${scene.scene_number}`}
              >
                <p className="text-[10px] font-semibold text-brand-amber">
                  S{scene.scene_number}
                </p>
                <p className="font-mono text-[10px] text-muted-foreground">
                  {formatSeconds(scene.start_time)}–{formatSeconds(scene.end_time)}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      <div className="space-y-4">
        {scenes.map((scene) => (
          <article
            key={scene.scene_number}
            className="rounded-xl border border-border bg-surface p-4"
            data-testid={`storyboard-v2-scene-${scene.scene_number}`}
          >
            <header className="flex flex-wrap items-start justify-between gap-2 border-b border-border pb-3">
              <div>
                <p className="text-sm font-semibold text-foreground">
                  Scene {scene.scene_number}
                </p>
                <p className="mt-0.5 font-mono text-xs text-muted-foreground">
                  {formatSeconds(scene.start_time)}–{formatSeconds(scene.end_time)}{" "}
                  · {scene.duration.toFixed(1)}s
                </p>
              </div>
              <div className="flex flex-wrap gap-2 text-[10px] uppercase tracking-wide">
                <span className="rounded-md bg-surface-elevated px-2 py-1 text-muted-foreground">
                  {scene.visual_type}
                </span>
                <span className="rounded-md bg-surface-elevated px-2 py-1 text-muted-foreground">
                  {scene.camera_movement}
                </span>
                <span className="rounded-md bg-surface-elevated px-2 py-1 text-muted-foreground">
                  {scene.music_mood}
                </span>
              </div>
            </header>
            <p className="mt-3 text-sm leading-relaxed text-foreground">
              {scene.narration}
            </p>
            <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-3">
              <div>
                <dt className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                  Scene goal
                </dt>
                <dd className="mt-1 text-muted-foreground">{scene.scene_goal}</dd>
              </div>
              <div>
                <dt className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                  Viewer emotion
                </dt>
                <dd className="mt-1 capitalize text-muted-foreground">
                  {scene.viewer_emotion.replaceAll("_", " ")}
                </dd>
              </div>
              <div>
                <dt className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                  Transition
                </dt>
                <dd className="mt-1 text-muted-foreground">{scene.transition}</dd>
              </div>
              <div>
                <dt className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                  Animation
                </dt>
                <dd className="mt-1 text-muted-foreground">
                  {scene.animation_suggestion}
                </dd>
              </div>
              <div>
                <dt className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                  On-screen text
                </dt>
                <dd className="mt-1 text-muted-foreground">
                  {scene.on_screen_text || "—"}{" "}
                  <span className="text-[10px] uppercase">
                    ({scene.text_position})
                  </span>
                </dd>
              </div>
              <div>
                <dt className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                  Asset required
                </dt>
                <dd className="mt-1 text-muted-foreground">{scene.asset_required}</dd>
              </div>
              <div>
                <dt className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                  SFX
                </dt>
                <dd className="mt-1 text-muted-foreground">{scene.sound_effects}</dd>
              </div>
              <div className="sm:col-span-2 lg:col-span-3">
                <dt className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                  Notes
                </dt>
                <dd className="mt-1 text-muted-foreground">{scene.notes}</dd>
              </div>
            </dl>
          </article>
        ))}
      </div>
    </div>
  );
}

function ShotListTab({ pkg }: { pkg: ProductionPackage }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-border">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead className="border-b border-border bg-surface-elevated text-xs uppercase tracking-wide text-muted-foreground">
          <tr>
            <th className="px-3 py-2">Shot</th>
            <th className="px-3 py-2">Scene</th>
            <th className="px-3 py-2">Type</th>
            <th className="px-3 py-2">Description</th>
            <th className="px-3 py-2">Flags</th>
            <th className="px-3 py-2">Priority</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border bg-surface">
          {pkg.shot_list.map((shot) => (
            <tr key={shot.shot_number}>
              <td className="px-3 py-3 tabular-nums">{shot.shot_number}</td>
              <td className="px-3 py-3">{shot.scene_number}</td>
              <td className="px-3 py-3">{shot.asset_type}</td>
              <td className="px-3 py-3 text-muted-foreground">
                {shot.description}
              </td>
              <td className="px-3 py-3 text-xs text-muted-foreground">
                {[
                  shot.illustration && "illustration",
                  shot.stock && "stock",
                  shot.diagram && "diagram",
                  shot.animation && "animation",
                  shot.text_overlay && "text",
                ]
                  .filter(Boolean)
                  .join(", ") || "—"}
              </td>
              <td className="px-3 py-3 capitalize">{shot.priority}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ChecklistTab({
  items,
}: {
  items: { id: string; label: string; required?: boolean; notes?: string | null; category?: string; domain?: string; checked?: boolean }[];
}) {
  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li
          key={item.id}
          className="flex items-start gap-3 rounded-lg border border-border bg-surface px-3 py-2 text-sm"
        >
          <span aria-hidden className="mt-0.5 text-muted-foreground">
            {item.checked ? "☑" : "☐"}
          </span>
          <div>
            <p className="text-foreground">
              {item.label}
              {item.required ? (
                <span className="ml-2 text-[10px] uppercase text-brand-amber">
                  Required
                </span>
              ) : null}
            </p>
            {item.notes ? (
              <p className="text-xs text-muted-foreground">{item.notes}</p>
            ) : null}
            {item.domain ? (
              <p className="text-[10px] uppercase tracking-wide text-muted-foreground">
                {item.domain}
              </p>
            ) : null}
          </div>
        </li>
      ))}
    </ul>
  );
}

export function ProductionPackagePage() {
  const params = useParams<{ projectId: string; scriptId: string }>();
  const projectId = params.projectId;
  const scriptId = params.scriptId;
  const [tab, setTab] = useState<TabId>("overview");
  const [generated, setGenerated] = useState(false);

  const scriptQuery = useScript(scriptId);
  const eligibilityQuery = useProductionPackageEligibility(scriptId);
  const createPackage = useCreateProductionPackage(scriptId);
  const packageQuery = useProductionPackage(scriptId, generated);

  const pkg = packageQuery.data ?? createPackage.data ?? undefined;
  const eligible = eligibilityQuery.data?.eligible === true;

  const errorMessage = useMemo(() => {
    const err = createPackage.error ?? packageQuery.error ?? eligibilityQuery.error;
    if (!err) return null;
    if (err instanceof ApiError) return err.detail;
    return "Unable to load production package.";
  }, [createPackage.error, packageQuery.error, eligibilityQuery.error]);

  async function onGenerate() {
    try {
      await createPackage.mutateAsync();
      setGenerated(true);
    } catch {
      /* surfaced via mutation error */
    }
  }

  if (scriptQuery.isLoading || eligibilityQuery.isLoading) {
    return (
      <PageContainer>
        <LoadingSkeleton className="h-40" />
      </PageContainer>
    );
  }

  if (scriptQuery.isError || !scriptQuery.data) {
    return (
      <PageContainer>
        <ErrorState message="Unable to load script." />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link
            href={`/projects/${projectId}/scripts/${scriptId}`}
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Workspace
          </Link>
          <h1 className="mt-2 flex items-center gap-2 text-2xl font-semibold tracking-tight">
            <Clapperboard className="h-6 w-6 text-brand-orange" aria-hidden />
            Production Package
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {scriptQuery.data.script_code} · {scriptQuery.data.title}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Planning only — no media generation or ZIP export.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            onClick={() => void onGenerate()}
            disabled={!eligible || createPackage.isPending}
            loading={createPackage.isPending}
            data-testid="generate-production-package"
          >
            {pkg ? (
              <>
                <RefreshCw className="h-4 w-4" />
                Regenerate Package
              </>
            ) : (
              "Generate Production Package"
            )}
          </Button>
        </div>
      </div>

      {!eligible ? (
        <EmptyState
          title="Gold approval required"
          description={
            eligibilityQuery.data?.reason ??
            "Approve the script, approve a content version, or reach a Gold quality review score (95+)."
          }
        />
      ) : null}

      {errorMessage ? <ErrorState message={errorMessage} /> : null}

      {createPackage.isPending && !pkg ? (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Building production package…
        </div>
      ) : null}

      {pkg ? (
        <>
          <div
            role="tablist"
            aria-label="Production package sections"
            className="mb-4 flex flex-wrap gap-2 border-b border-border pb-2"
          >
            {TABS.map((id) => (
              <button
                key={id}
                type="button"
                role="tab"
                aria-selected={tab === id}
                className={
                  tab === id
                    ? "rounded-md bg-brand-orange/15 px-3 py-1.5 text-sm font-medium text-brand-amber"
                    : "rounded-md px-3 py-1.5 text-sm text-muted-foreground hover:bg-surface-hover hover:text-foreground"
                }
                onClick={() => setTab(id)}
              >
                {TAB_LABELS[id]}
              </button>
            ))}
          </div>

          <div role="tabpanel">
            {tab === "overview" ? <OverviewTab pkg={pkg} /> : null}
            {tab === "storyboard" ? <StoryboardTab pkg={pkg} /> : null}
            {tab === "storyboard_v2" ? <StoryboardV2Tab pkg={pkg} /> : null}
            {tab === "shot_list" ? <ShotListTab pkg={pkg} /> : null}
            {tab === "assets" ? (
              <ChecklistTab items={pkg.asset_checklist} />
            ) : null}
            {tab === "voice" ? (
              <div className="space-y-3 rounded-xl border border-border bg-surface p-4 text-sm">
                <p>
                  Duration ~{pkg.voice_package.estimated_duration_seconds}s ·{" "}
                  {pkg.voice_package.word_count} words ·{" "}
                  {pkg.voice_package.recommended_wpm} WPM
                </p>
                <p className="text-muted-foreground">
                  Persona: {pkg.voice_package.persona_hint}
                </p>
                <div>
                  <h3 className="font-semibold">Pause markers</h3>
                  <ul className="mt-1 list-disc pl-5 text-muted-foreground">
                    {pkg.voice_package.pause_markers.map((m) => (
                      <li key={m}>{m}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3 className="font-semibold">Emphasis markers</h3>
                  <ul className="mt-1 list-disc pl-5 text-muted-foreground">
                    {pkg.voice_package.emphasis_markers.map((m) => (
                      <li key={m}>{m}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3 className="font-semibold">Pronunciation notes</h3>
                  <ul className="mt-1 list-disc pl-5 text-muted-foreground">
                    {pkg.voice_package.pronunciation_notes.map((m) => (
                      <li key={m}>{m}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : null}
            {tab === "subtitles" ? (
              <div className="overflow-x-auto rounded-xl border border-border">
                <table className="w-full min-w-[640px] text-left text-sm">
                  <thead className="border-b border-border bg-surface-elevated text-xs uppercase text-muted-foreground">
                    <tr>
                      <th className="px-3 py-2">#</th>
                      <th className="px-3 py-2">Time</th>
                      <th className="px-3 py-2">Lines</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border bg-surface">
                    {pkg.subtitle_package.map((seg) => (
                      <tr key={seg.index}>
                        <td className="px-3 py-2">{seg.index}</td>
                        <td className="px-3 py-2 font-mono text-xs">
                          {seg.start_seconds.toFixed(1)}s–{seg.end_seconds.toFixed(1)}s
                        </td>
                        <td className="px-3 py-2">
                          {seg.lines.map((line) => (
                            <div key={line}>{line}</div>
                          ))}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
            {tab === "youtube" ? (
              <div className="space-y-3 rounded-xl border border-border bg-surface p-4 text-sm">
                <div>
                  <h3 className="font-semibold">Title</h3>
                  <p>{pkg.youtube_package.title}</p>
                </div>
                <div>
                  <h3 className="font-semibold">Description</h3>
                  <PreBlock text={pkg.youtube_package.description} />
                </div>
                <div>
                  <h3 className="font-semibold">Keywords</h3>
                  <p className="text-muted-foreground">
                    {pkg.youtube_package.keywords.join(", ")}
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold">Hashtags</h3>
                  <p className="text-muted-foreground">
                    {pkg.youtube_package.hashtags.join(" ")}
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold">Category</h3>
                  <p>{pkg.youtube_package.category}</p>
                </div>
                <div>
                  <h3 className="font-semibold">Thumbnail concept</h3>
                  <p className="text-muted-foreground">
                    {pkg.youtube_package.thumbnail_concept}
                  </p>
                </div>
              </div>
            ) : null}
            {tab === "qa" ? <ChecklistTab items={pkg.qa_package} /> : null}
          </div>
        </>
      ) : null}
    </PageContainer>
  );
}
