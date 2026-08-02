/**
 * Client helpers for Script AI Quality Review structured output.
 */

import type {
  AiGeneration,
  ScriptQualityBand,
  ScriptQualityConfidence,
  ScriptQualityDimensionKey,
  ScriptQualityDimensionReview,
  ScriptQualityFactualRisk,
  ScriptQualityPacingAnalysis,
  ScriptQualityPacingStatus,
  ScriptQualityPriorityIssue,
  ScriptQualityPromiseAnalysis,
  ScriptQualityRecommendation,
  ScriptQualityReview,
  ScriptQualityRiskLevel,
  ScriptQualitySeverity,
} from "@/lib/ai/types";
import {
  SCRIPT_QUALITY_DIMENSIONS,
  SCRIPT_QUALITY_REVIEW_PURPOSE,
} from "@/lib/ai/types";

const SEVERITY_ORDER: Record<ScriptQualitySeverity, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
};

export const QUALITY_BAND_LABELS: Record<ScriptQualityBand, string> = {
  excellent: "Excellent",
  strong: "Strong",
  needs_refinement: "Needs Refinement",
  weak: "Weak",
  major_revision_required: "Major Revision Required",
};

/** Advisory next-action labels — never "Approved". */
export const RECOMMENDATION_LABELS: Record<ScriptQualityRecommendation, string> =
  {
    revise: "Revise",
    human_review: "Ready for Human Review",
    ready_for_version: "Ready for Version",
  };

export const DIMENSION_LABELS: Record<ScriptQualityDimensionKey, string> = {
  hook: "Hook",
  curiosity: "Curiosity",
  retention: "Retention",
  clarity: "Clarity",
  structure: "Structure",
  factual_safety: "Factual Safety",
  viewer_promise: "Viewer Promise",
  payoff: "Payoff",
  pacing: "Pacing",
  spoken_naturalness: "Spoken Naturalness",
  conciseness: "Conciseness",
  brand_voice: "Brand Voice",
  call_to_action: "Call to Action",
  duration_fit: "Duration Fit",
};

export const PACING_STATUS_LABELS: Record<ScriptQualityPacingStatus, string> = {
  short: "Short",
  within_range: "Within range",
  long: "Long",
};

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => (typeof item === "string" ? item.trim() : ""))
    .filter(Boolean);
}

function asNumber(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function asBoolean(value: unknown, fallback = false): boolean {
  return typeof value === "boolean" ? value : fallback;
}

function asSeverity(value: unknown): ScriptQualitySeverity {
  if (value === "critical" || value === "high" || value === "medium" || value === "low") {
    return value;
  }
  return "medium";
}

function asRiskLevel(value: unknown): ScriptQualityRiskLevel {
  if (value === "high" || value === "medium" || value === "low") return value;
  return "medium";
}

function asConfidence(value: unknown): ScriptQualityConfidence {
  if (value === "high" || value === "medium" || value === "low") return value;
  return "medium";
}

function asPacingStatus(value: unknown): ScriptQualityPacingStatus {
  if (value === "short" || value === "within_range" || value === "long") {
    return value;
  }
  return "within_range";
}

function asBand(value: unknown): ScriptQualityBand {
  if (
    value === "excellent" ||
    value === "strong" ||
    value === "needs_refinement" ||
    value === "weak" ||
    value === "major_revision_required"
  ) {
    return value;
  }
  return "needs_refinement";
}

function asRecommendation(value: unknown): ScriptQualityRecommendation {
  if (
    value === "revise" ||
    value === "human_review" ||
    value === "ready_for_version"
  ) {
    return value;
  }
  return "human_review";
}

function parseDimension(value: unknown): ScriptQualityDimensionReview {
  const row = value && typeof value === "object" ? (value as Record<string, unknown>) : {};
  return {
    score: Math.max(0, Math.min(100, asNumber(row.score, 0))),
    assessment: asString(row.assessment).trim(),
    strengths: asStringArray(row.strengths),
    issues: asStringArray(row.issues),
    suggested_action: asString(row.suggested_action).trim(),
  };
}

function parseIssue(value: unknown): ScriptQualityPriorityIssue | null {
  if (!value || typeof value !== "object") return null;
  const row = value as Record<string, unknown>;
  const id = asString(row.id).trim();
  if (!id) return null;
  const rewriteRaw = row.suggested_rewrite;
  const rewrite =
    typeof rewriteRaw === "string" && rewriteRaw.trim()
      ? rewriteRaw.trim()
      : null;
  return {
    id,
    severity: asSeverity(row.severity),
    category: asString(row.category).trim() || "clarity",
    location_hint: asString(row.location_hint).trim(),
    original_excerpt: asString(row.original_excerpt).trim(),
    problem: asString(row.problem).trim(),
    recommended_change: asString(row.recommended_change).trim(),
    suggested_rewrite: rewrite,
  };
}

function parseRisk(value: unknown): ScriptQualityFactualRisk | null {
  if (!value || typeof value !== "object") return null;
  const row = value as Record<string, unknown>;
  const claim = asString(row.claim).trim();
  if (!claim) return null;
  const note = row.related_source_note;
  return {
    claim,
    risk_level: asRiskLevel(row.risk_level),
    reason: asString(row.reason).trim(),
    verification_needed: true,
    related_source_note:
      typeof note === "string" && note.trim() ? note.trim() : null,
  };
}

function parsePacing(value: unknown): ScriptQualityPacingAnalysis {
  const row = value && typeof value === "object" ? (value as Record<string, unknown>) : {};
  return {
    estimated_word_count: asNumber(row.estimated_word_count, 0),
    estimated_duration_seconds: asNumber(row.estimated_duration_seconds, 0),
    target_duration_seconds: asNumber(row.target_duration_seconds, 60),
    target_words_per_minute:
      row.target_words_per_minute == null
        ? undefined
        : asNumber(row.target_words_per_minute, 150),
    status: asPacingStatus(row.status),
    slow_sections: asStringArray(row.slow_sections),
    rushed_sections: asStringArray(row.rushed_sections),
    source: asString(row.source).trim() || undefined,
  };
}

function parsePromise(value: unknown): ScriptQualityPromiseAnalysis {
  const row = value && typeof value === "object" ? (value as Record<string, unknown>) : {};
  return {
    promise_made: asString(row.promise_made).trim(),
    promise_delivered: asBoolean(row.promise_delivered, false),
    explanation: asString(row.explanation).trim(),
  };
}

export function isScriptQualityReviewPurpose(
  purpose: string | null | undefined,
): boolean {
  return purpose === SCRIPT_QUALITY_REVIEW_PURPOSE;
}

export function parseScriptQualityReview(
  payload: unknown,
): ScriptQualityReview | null {
  if (!payload || typeof payload !== "object") return null;
  const raw = payload as Record<string, unknown>;
  if (!raw.dimensions || typeof raw.dimensions !== "object") return null;
  if (!raw.pacing_analysis || typeof raw.pacing_analysis !== "object") return null;

  const dimSource = raw.dimensions as Record<string, unknown>;
  const dimensions: Record<string, ScriptQualityDimensionReview> = {};
  for (const key of SCRIPT_QUALITY_DIMENSIONS) {
    if (!(key in dimSource)) return null;
    dimensions[key] = parseDimension(dimSource[key]);
  }

  const overall = Math.max(0, Math.min(100, asNumber(raw.overall_score, 0)));
  const band = asBand(raw.quality_band);
  const bandLabel =
    asString(raw.quality_band_label).trim() || QUALITY_BAND_LABELS[band];

  const issues = Array.isArray(raw.priority_issues)
    ? raw.priority_issues
        .map(parseIssue)
        .filter((item): item is ScriptQualityPriorityIssue => item != null)
    : [];

  const risks = Array.isArray(raw.factual_risks)
    ? raw.factual_risks
        .map(parseRisk)
        .filter((item): item is ScriptQualityFactualRisk => item != null)
    : [];

  const metricsRaw = raw.deterministic_metrics;
  const metrics =
    metricsRaw && typeof metricsRaw === "object"
      ? {
          word_count: asNumber(
            (metricsRaw as Record<string, unknown>).word_count,
            0,
          ),
          estimated_duration_seconds: asNumber(
            (metricsRaw as Record<string, unknown>).estimated_duration_seconds,
            0,
          ),
          target_duration_seconds: asNumber(
            (metricsRaw as Record<string, unknown>).target_duration_seconds,
            60,
          ),
          target_words_per_minute: asNumber(
            (metricsRaw as Record<string, unknown>).target_words_per_minute,
            150,
          ),
          pacing_status: asPacingStatus(
            (metricsRaw as Record<string, unknown>).pacing_status,
          ),
          master_script_fingerprint:
            asString(
              (metricsRaw as Record<string, unknown>).master_script_fingerprint,
            ).trim() || undefined,
        }
      : undefined;

  return {
    overall_score: overall,
    model_overall_score:
      raw.model_overall_score == null
        ? undefined
        : asNumber(raw.model_overall_score, overall),
    calculated_overall_score:
      raw.calculated_overall_score == null
        ? undefined
        : asNumber(raw.calculated_overall_score, overall),
    quality_band: band,
    quality_band_label: bandLabel,
    confidence: asConfidence(raw.confidence),
    summary: asString(raw.summary).trim(),
    ready_for_human_review: asBoolean(raw.ready_for_human_review, false),
    dimensions,
    priority_issues: sortPriorityIssues(issues),
    factual_risks: risks,
    pacing_analysis: parsePacing(raw.pacing_analysis),
    promise_analysis: parsePromise(raw.promise_analysis),
    recommended_next_action: asRecommendation(raw.recommended_next_action),
    deterministic_metrics: metrics,
    score_weights:
      raw.score_weights && typeof raw.score_weights === "object"
        ? Object.fromEntries(
            Object.entries(raw.score_weights as Record<string, unknown>).map(
              ([key, value]) => [key, asNumber(value, 0)],
            ),
          )
        : undefined,
    warnings: asStringArray(raw.warnings),
    ai_approval: false,
  };
}

export function qualityReviewFromGeneration(
  generation: AiGeneration | null | undefined,
): ScriptQualityReview | null {
  if (!generation) return null;
  return parseScriptQualityReview(generation.structured_output);
}

export function sortPriorityIssues(
  issues: ScriptQualityPriorityIssue[],
): ScriptQualityPriorityIssue[] {
  return [...issues].sort((a, b) => {
    const sev =
      (SEVERITY_ORDER[a.severity] ?? 99) - (SEVERITY_ORDER[b.severity] ?? 99);
    if (sev !== 0) return sev;
    return a.id.localeCompare(b.id);
  });
}

export function recommendationLabel(
  action: ScriptQualityRecommendation | string | null | undefined,
): string {
  if (action === "revise" || action === "human_review" || action === "ready_for_version") {
    return RECOMMENDATION_LABELS[action];
  }
  return "Ready for Human Review";
}

export function dimensionLabel(key: string): string {
  if (key in DIMENSION_LABELS) {
    return DIMENSION_LABELS[key as ScriptQualityDimensionKey];
  }
  return key.replaceAll("_", " ");
}

export function issueAppliedKey(issueId: string): string {
  return `issue:${issueId}`;
}

export function isIssueApplied(
  generation: AiGeneration | null | undefined,
  issueId: string,
): boolean {
  const sections = generation?.applied_sections ?? [];
  return sections.includes(issueAppliedKey(issueId));
}

export function qualityReviewHref(
  projectId: string,
  scriptId: string,
  generationId: string,
): string {
  return `/projects/${projectId}/scripts/${scriptId}/quality-reviews/${generationId}`;
}
