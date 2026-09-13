"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  Sparkles,
  ExternalLink,
  Copy,
  Check,
  Calendar,
  AlertTriangle,
  HelpCircle,
  ThumbsUp,
  Edit3,
  XCircle,
  Clock,
  Send,
  BarChart2,
  RefreshCw,
  Info,
} from "lucide-react";
import { api } from "@/lib/api";
import type {
  Recommendation,
  ReviewDecision,
  FeedbackScope,
  ReviewInput,
  ActionPerformedInput,
  MetricsInput,
} from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/Card";
import { Modal } from "@/components/ui/Modal";
import { Textarea } from "@/components/ui/Textarea";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";

export default function RecommendationsPage() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Modals state
  const [editModalRec, setEditModalRec] = useState<Recommendation | null>(null);
  const [editText, setEditText] = useState("");
  const [editReasonCategory, setEditReasonCategory] = useState("sounds_unlike_me");
  const [editReasonText, setEditReasonText] = useState("");
  const [editScope, setEditScope] = useState<FeedbackScope>("this_only");

  const [rejectModalRec, setRejectModalRec] = useState<Recommendation | null>(null);
  const [rejectReasonCategory, setRejectReasonCategory] = useState("not_useful");
  const [rejectReasonText, setRejectReasonText] = useState("");
  const [rejectScope, setRejectScope] = useState<FeedbackScope>("this_only");

  const [laterModalRec, setLaterModalRec] = useState<Recommendation | null>(null);
  const [postponeDate, setPostponeDate] = useState("");

  const [performedModalRec, setPerformedModalRec] = useState<Recommendation | null>(null);
  const [performedUrl, setPerformedUrl] = useState("");
  const [performedNotes, setPerformedNotes] = useState("");

  const [metricsModalAction, setMetricsModalAction] = useState<{ id: string; title: string } | null>(null);
  const [metricImpressions, setMetricImpressions] = useState("");
  const [metricLikes, setMetricLikes] = useState("");
  const [metricReplies, setMetricReplies] = useState("");

  const [errorBanner, setErrorBanner] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setSuccessToast(msg);
    setTimeout(() => setSuccessToast(null), 4000);
  };

  const loadRecommendations = useCallback(async () => {
    setIsLoading(true);
    setErrorBanner(null);
    try {
      const data = await api.getRecommendations();
      setRecommendations(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load recommendations";
      setErrorBanner(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRecommendations();
  }, [loadRecommendations]);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setErrorBanner(null);
    try {
      const res = await api.startWorkflow("recommendation_review", {
        topic: "Technical Architecture and Engineering Practice",
      });
      showToast("Generated new recommendations based on current profile and research.");
      if (res.recommendations && res.recommendations.length > 0) {
        setRecommendations(res.recommendations);
      } else {
        await loadRecommendations();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to generate recommendations";
      setErrorBanner(msg);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApprove = async (rec: Recommendation) => {
    try {
      const updated = await api.reviewRecommendation(rec.id, {
        decision: "approve",
        scope: "this_only",
      });
      setRecommendations((prev) => prev.map((r) => (r.id === rec.id ? updated : r)));
      showToast("Recommendation approved. Ready for manual publication.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to approve recommendation";
      setErrorBanner(msg);
    }
  };

  const submitEdit = async () => {
    if (!editModalRec) return;
    try {
      const review: ReviewInput = {
        decision: "edit",
        final_text: editText,
        reason_category: editReasonCategory,
        reason_text: editReasonText || undefined,
        scope: editScope,
      };
      const updated = await api.reviewRecommendation(editModalRec.id, review);
      setRecommendations((prev) => prev.map((r) => (r.id === editModalRec.id ? updated : r)));
      setEditModalRec(null);
      showToast("Changes saved. Recommendation approved with your edits.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save edits";
      setErrorBanner(msg);
    }
  };

  const submitReject = async () => {
    if (!rejectModalRec) return;
    try {
      const review: ReviewInput = {
        decision: "reject",
        reason_category: rejectReasonCategory,
        reason_text: rejectReasonText || undefined,
        scope: rejectScope,
      };
      const updated = await api.reviewRecommendation(rejectModalRec.id, review);
      setRecommendations((prev) => prev.map((r) => (r.id === rejectModalRec.id ? updated : r)));
      setRejectModalRec(null);
      showToast("Recommendation rejected. Feedback will improve future suggestions.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to reject";
      setErrorBanner(msg);
    }
  };

  const submitLater = async () => {
    if (!laterModalRec) return;
    try {
      const review: ReviewInput = {
        decision: "later",
        postpone_until: postponeDate ? new Date(postponeDate).toISOString() : undefined,
      };
      const updated = await api.reviewRecommendation(laterModalRec.id, review);
      setRecommendations((prev) => prev.map((r) => (r.id === laterModalRec.id ? updated : r)));
      setLaterModalRec(null);
      showToast("Postponed recommendation.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to postpone";
      setErrorBanner(msg);
    }
  };

  const submitPerformed = async () => {
    if (!performedModalRec) return;
    try {
      const payload: ActionPerformedInput = {
        public_url: performedUrl || undefined,
        notes: performedNotes || undefined,
      };
      await api.reportPerformed(performedModalRec.id, payload);
      setPerformedModalRec(null);
      await loadRecommendations();
      showToast("Marked as performed. Measurement scheduled in 24 hours.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to report performed";
      setErrorBanner(msg);
    }
  };

  const submitMetrics = async () => {
    if (!metricsModalAction) return;
    try {
      const metrics: Record<string, number | null> = {};
      if (metricImpressions) metrics["impressions"] = parseInt(metricImpressions, 10);
      if (metricLikes) metrics["likes"] = parseInt(metricLikes, 10);
      if (metricReplies) metrics["replies"] = parseInt(metricReplies, 10);

      const payload: MetricsInput = {
        metrics,
        source: "user_reported",
      };
      await api.addMetrics(metricsModalAction.id, payload);
      setMetricsModalAction(null);
      setMetricImpressions("");
      setMetricLikes("");
      setMetricReplies("");
      showToast("Metrics recorded successfully.");
      await loadRecommendations();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to record metrics";
      setErrorBanner(msg);
    }
  };

  const copyToClipboard = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2500);
      showToast("Clean text copied to clipboard!");
    } catch {
      // Fallback
    }
  };

  const getPlatformBadgeVariant = (platform: string | null) => {
    if (platform === "github") return "github";
    if (platform === "x") return "x";
    if (platform === "linkedin") return "linkedin";
    return "default";
  };

  return (
    <div className="space-y-6">
      {/* Toast Alert */}
      {successToast && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-3 text-sm font-medium text-white shadow-xl shadow-emerald-950/40">
          <Check className="h-4 w-4" />
          <span>{successToast}</span>
        </div>
      )}

      {/* Error Banner */}
      {errorBanner && (
        <div className="flex items-center justify-between rounded-xl border border-rose-800/80 bg-rose-950/40 p-4 text-sm text-rose-200">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-rose-400" />
            <span>{errorBanner}</span>
          </div>
          <button
            onClick={() => setErrorBanner(null)}
            className="text-xs text-rose-400 hover:text-rose-200"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
              Daily Recommendations & Review
            </h1>
            <Badge variant="primary" size="sm">Workflows D & E</Badge>
          </div>
          <p className="mt-1 text-sm text-zinc-400">
            Carefully curated technical actions grounded in real evidence. Human review required for all public steps.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadRecommendations}
            isLoading={isLoading}
          >
            <RefreshCw className="h-3.5 w-3.5 mr-1" />
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleGenerate}
            isLoading={isGenerating}
          >
            <Sparkles className="h-3.5 w-3.5 mr-1" />
            Generate Daily Brief
          </Button>
        </div>
      </div>

      {/* Recommendations Feed */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-16 text-zinc-500">
          <RefreshCw className="h-8 w-8 animate-spin text-indigo-500 mb-3" />
          <p className="text-sm">Loading daily recommendations...</p>
        </div>
      ) : recommendations.length === 0 ? (
        <Card className="text-center py-12">
          <div className="max-w-md mx-auto space-y-3">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-zinc-800 text-zinc-400">
              <Sparkles className="h-6 w-6 text-indigo-400" />
            </div>
            <h3 className="text-base font-semibold text-zinc-100">
              No Pending Recommendations Today
            </h3>
            <p className="text-sm text-zinc-400 leading-relaxed">
              When quality, evidence, or timing is insufficient, the system recommends taking no action to protect your professional credibility.
            </p>
            <div className="pt-2">
              <Button
                variant="primary"
                onClick={handleGenerate}
                isLoading={isGenerating}
              >
                Trigger Recommendation Workflow
              </Button>
            </div>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {recommendations.map((rec) => {
            const isApproved = rec.status === "approved" || rec.status === "edited";
            const isPerformed = rec.status === "reported_performed" || rec.status === "verified_performed";
            const isRejected = rec.status === "rejected";
            const isPostponed = rec.status === "postponed";
            const textToPublish = rec.final_text || rec.draft || "";

            return (
              <Card
                key={rec.id}
                variant={isApproved ? "highlight" : "default"}
                className={`transition-all ${isRejected ? "opacity-60 bg-zinc-950" : ""}`}
              >
                <CardHeader>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="primary">{rec.action_type.replace(/_/g, " ").toUpperCase()}</Badge>
                      {rec.platform && (
                        <Badge variant={getPlatformBadgeVariant(rec.platform)}>
                          {rec.platform.toUpperCase()}
                        </Badge>
                      )}
                      <Badge
                        variant={
                          isApproved
                            ? "success"
                            : isPerformed
                            ? "info"
                            : isRejected
                            ? "danger"
                            : isPostponed
                            ? "warning"
                            : "default"
                        }
                      >
                        {rec.status.replace(/_/g, " ")}
                      </Badge>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-zinc-400">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        ~{rec.effort_minutes} mins
                      </span>
                      <span>Score: {Math.round(rec.score * 100)}%</span>
                    </div>
                  </div>

                  <CardTitle className="mt-2 text-xl">{rec.title}</CardTitle>
                  <CardDescription className="text-zinc-300 font-medium">
                    Purpose: {rec.purpose}
                  </CardDescription>
                </CardHeader>

                <CardContent className="space-y-4">
                  {/* Context & Why Now */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <div className="rounded-lg bg-zinc-950/60 p-2.5 border border-zinc-800/80">
                      <span className="text-zinc-500 font-medium block">Target Audience</span>
                      <span className="text-zinc-300 mt-0.5 block">{rec.target_audience}</span>
                    </div>
                    <div className="rounded-lg bg-zinc-950/60 p-2.5 border border-zinc-800/80">
                      <span className="text-zinc-500 font-medium block">Why Now</span>
                      <span className="text-zinc-300 mt-0.5 block">{rec.why_now}</span>
                    </div>
                  </div>

                  {/* Draft text box */}
                  {textToPublish && (
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs text-zinc-400">
                        <span className="font-medium">
                          {rec.final_text ? "User-Approved Final Copy" : "Proposed Draft"}
                        </span>
                        <button
                          onClick={() => copyToClipboard(textToPublish, rec.id)}
                          className="flex items-center gap-1 text-indigo-400 hover:text-indigo-300"
                        >
                          {copiedId === rec.id ? (
                            <>
                              <Check className="h-3.5 w-3.5 text-emerald-400" />
                              <span className="text-emerald-400">Copied!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="h-3.5 w-3.5" />
                              <span>Copy Text</span>
                            </>
                          )}
                        </button>
                      </div>
                      <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3.5 text-sm text-zinc-200 font-mono whitespace-pre-wrap leading-relaxed">
                        {textToPublish}
                      </div>
                    </div>
                  )}

                  {/* Evidence & Risks Accordion */}
                  <div className="rounded-lg border border-zinc-800/60 bg-zinc-950/40 p-3 text-xs space-y-2">
                    <div className="flex items-center gap-2 font-medium text-zinc-300">
                      <Info className="h-3.5 w-3.5 text-indigo-400" />
                      <span>Evidence Grounding & Safety Checks</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-zinc-400">
                      <div>
                        <span className="text-zinc-500 block">Supporting Memories:</span>
                        <span>{rec.evidence_ids.length > 0 ? rec.evidence_ids.join(", ") : "Grounded via profile context"}</span>
                      </div>
                      {rec.source_urls.length > 0 && (
                        <div>
                          <span className="text-zinc-500 block">Source References:</span>
                          <span className="truncate block">{rec.source_urls.join(", ")}</span>
                        </div>
                      )}
                    </div>
                    {rec.risks.length > 0 && (
                      <div className="text-amber-400 flex items-start gap-1 mt-1">
                        <AlertTriangle className="h-3.5 w-3.5 flex-shrink-0 mt-0.5" />
                        <span>Risks: {rec.risks.join("; ")}</span>
                      </div>
                    )}
                    {rec.unknowns.length > 0 && (
                      <div className="text-zinc-400 flex items-start gap-1">
                        <HelpCircle className="h-3.5 w-3.5 flex-shrink-0 mt-0.5" />
                        <span>Unknowns: {rec.unknowns.join("; ")}</span>
                      </div>
                    )}
                  </div>
                </CardContent>

                <CardFooter>
                  {/* Actions depending on state */}
                  {!isApproved && !isPerformed && !isRejected && (
                    <div className="flex flex-wrap items-center gap-2 w-full justify-between">
                      <div className="flex items-center gap-2">
                        <Button
                          variant="success"
                          size="sm"
                          onClick={() => handleApprove(rec)}
                        >
                          <ThumbsUp className="h-3.5 w-3.5 mr-1" />
                          Approve
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setEditModalRec(rec);
                            setEditText(textToPublish);
                          }}
                        >
                          <Edit3 className="h-3.5 w-3.5 mr-1" />
                          Edit
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setLaterModalRec(rec)}
                        >
                          <Clock className="h-3.5 w-3.5 mr-1" />
                          Later
                        </Button>
                      </div>

                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-rose-400 hover:text-rose-300"
                        onClick={() => setRejectModalRec(rec)}
                      >
                        <XCircle className="h-3.5 w-3.5 mr-1" />
                        Reject
                      </Button>
                    </div>
                  )}

                  {isApproved && !isPerformed && (
                    <div className="flex flex-wrap items-center justify-between gap-3 w-full">
                      <div className="flex items-center gap-2 text-xs text-emerald-400 font-medium">
                        <Check className="h-4 w-4" />
                        <span>Approved by you. Manual execution required.</span>
                      </div>

                      <div className="flex items-center gap-2">
                        {rec.platform === "x" && (
                          <a
                            href={`https://x.com/intent/post?text=${encodeURIComponent(textToPublish)}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs font-medium text-zinc-200 hover:bg-zinc-800"
                          >
                            <ExternalLink className="h-3.5 w-3.5" />
                            Open on X
                          </a>
                        )}
                        {rec.platform === "linkedin" && (
                          <a
                            href="https://www.linkedin.com/feed/"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs font-medium text-zinc-200 hover:bg-zinc-800"
                          >
                            <ExternalLink className="h-3.5 w-3.5" />
                            Open LinkedIn
                          </a>
                        )}
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => {
                            setPerformedModalRec(rec);
                            setPerformedUrl("");
                            setPerformedNotes("");
                          }}
                        >
                          <Send className="h-3.5 w-3.5 mr-1" />
                          Mark as Performed
                        </Button>
                      </div>
                    </div>
                  )}

                  {isPerformed && (
                    <div className="flex items-center justify-between w-full">
                      <div className="flex items-center gap-2 text-xs text-sky-400 font-medium">
                        <Check className="h-4 w-4" />
                        <span>Performed. Measurement scheduled.</span>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          setMetricsModalAction({
                            id: rec.id,
                            title: rec.title,
                          })
                        }
                      >
                        <BarChart2 className="h-3.5 w-3.5 mr-1" />
                        Record 24h Metrics
                      </Button>
                    </div>
                  )}
                </CardFooter>
              </Card>
            );
          })}
        </div>
      )}

      {/* Edit Modal */}
      <Modal
        isOpen={Boolean(editModalRec)}
        onClose={() => setEditModalRec(null)}
        title="Edit Recommendation Draft"
        description="Your changes will be saved as the authoritative version and will refine future suggestions."
      >
        <div className="space-y-4">
          <Textarea
            label="Adjust Draft Text"
            rows={5}
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
          />

          <Select
            label="Why are you making this change?"
            value={editReasonCategory}
            onChange={(e) => setEditReasonCategory(e.target.value)}
            options={[
              { value: "sounds_unlike_me", label: "Sounds unlike me / Voice mismatch" },
              { value: "too_polished", label: "Too polished or formal" },
              { value: "too_generic", label: "Too generic / Lacks depth" },
              { value: "inaccurate", label: "Inaccurate or exaggerated claim" },
              { value: "not_my_opinion", label: "Not my actual technical stance" },
              { value: "wrong_audience", label: "Wrong target audience or niche" },
              { value: "clearer_explanation", label: "Clearer technical explanation" },
              { value: "other", label: "Other reason" },
            ]}
          />

          <Input
            label="Optional Note"
            placeholder="e.g., I prefer using concrete benchmark examples instead of general terms"
            value={editReasonText}
            onChange={(e) => setEditReasonText(e.target.value)}
          />

          <Select
            label="Apply Feedback Scope"
            value={editScope}
            onChange={(e) => setEditScope(e.target.value as FeedbackScope)}
            options={[
              { value: "this_only", label: "This recommendation only" },
              { value: "similar", label: "Similar recommendations in this niche" },
              { value: "general", label: "General writing style preference" },
            ]}
          />

          <div className="flex justify-end gap-2 pt-3 border-t border-zinc-800">
            <Button variant="ghost" onClick={() => setEditModalRec(null)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={submitEdit}>
              Save & Approve
            </Button>
          </div>
        </div>
      </Modal>

      {/* Reject Modal */}
      <Modal
        isOpen={Boolean(rejectModalRec)}
        onClose={() => setRejectModalRec(null)}
        title="Reject Recommendation"
        description="Help the agent understand why this does not fit so it stops suggesting similar items."
      >
        <div className="space-y-4">
          <Select
            label="Reason for Rejection"
            value={rejectReasonCategory}
            onChange={(e) => setRejectReasonCategory(e.target.value)}
            options={[
              { value: "not_useful", label: "Not useful or interesting enough" },
              { value: "do_not_want_interaction", label: "Do not want to interact with this person/group" },
              { value: "already_covered", label: "I have already covered this recently" },
              { value: "too_much_effort", label: "Too much effort right now" },
              { value: "not_my_opinion", label: "Disagree with the underlying premise" },
              { value: "other", label: "Other" },
            ]}
          />

          <Input
            label="Optional Detail"
            placeholder="Provide context if helpful"
            value={rejectReasonText}
            onChange={(e) => setRejectReasonText(e.target.value)}
          />

          <Select
            label="Feedback Scope"
            value={rejectScope}
            onChange={(e) => setRejectScope(e.target.value as FeedbackScope)}
            options={[
              { value: "this_only", label: "This recommendation only" },
              { value: "similar", label: "Similar recommendations" },
              { value: "general", label: "General rule" },
            ]}
          />

          <div className="flex justify-end gap-2 pt-3 border-t border-zinc-800">
            <Button variant="ghost" onClick={() => setRejectModalRec(null)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={submitReject}>
              Confirm Rejection
            </Button>
          </div>
        </div>
      </Modal>

      {/* Later / Postpone Modal */}
      <Modal
        isOpen={Boolean(laterModalRec)}
        onClose={() => setLaterModalRec(null)}
        title="Postpone Recommendation"
        description="Keep this idea and bring it back when timing is better."
      >
        <div className="space-y-4">
          <Input
            label="Postpone Until"
            type="datetime-local"
            value={postponeDate}
            onChange={(e) => setPostponeDate(e.target.value)}
          />
          <div className="flex justify-end gap-2 pt-3 border-t border-zinc-800">
            <Button variant="ghost" onClick={() => setLaterModalRec(null)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={submitLater}>
              Postpone
            </Button>
          </div>
        </div>
      </Modal>

      {/* Performed Modal */}
      <Modal
        isOpen={Boolean(performedModalRec)}
        onClose={() => setPerformedModalRec(null)}
        title="Mark Action as Performed"
        description="Record that you published this action so the system can measure real audience response."
      >
        <div className="space-y-4">
          <Input
            label="Public Post URL (Optional)"
            placeholder="https://x.com/yourusername/status/..."
            value={performedUrl}
            onChange={(e) => setPerformedUrl(e.target.value)}
          />
          <Textarea
            label="Notes or Observations (Optional)"
            placeholder="Any notable early replies, interesting discussion, or thoughts..."
            rows={3}
            value={performedNotes}
            onChange={(e) => setPerformedNotes(e.target.value)}
          />
          <div className="flex justify-end gap-2 pt-3 border-t border-zinc-800">
            <Button variant="ghost" onClick={() => setPerformedModalRec(null)}>
              Cancel
            </Button>
            <Button variant="success" onClick={submitPerformed}>
              Confirm Action Performed
            </Button>
          </div>
        </div>
      </Modal>

      {/* Metrics Modal */}
      <Modal
        isOpen={Boolean(metricsModalAction)}
        onClose={() => setMetricsModalAction(null)}
        title="Record 24h Outcome Metrics"
        description="Record real metrics from X or LinkedIn to test hypotheses and improve strategy."
      >
        <div className="space-y-4">
          <Input
            label="Impressions / Views"
            type="number"
            placeholder="e.g., 1200"
            value={metricImpressions}
            onChange={(e) => setMetricImpressions(e.target.value)}
          />
          <Input
            label="Likes / Reactions"
            type="number"
            placeholder="e.g., 45"
            value={metricLikes}
            onChange={(e) => setMetricLikes(e.target.value)}
          />
          <Input
            label="Replies / Comments"
            type="number"
            placeholder="e.g., 8"
            value={metricReplies}
            onChange={(e) => setMetricReplies(e.target.value)}
          />
          <div className="flex justify-end gap-2 pt-3 border-t border-zinc-800">
            <Button variant="ghost" onClick={() => setMetricsModalAction(null)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={submitMetrics}>
              Save Metrics
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

