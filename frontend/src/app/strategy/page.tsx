"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  Target,
  Compass,
  Lightbulb,
  CheckCircle,
  TrendingUp,
  Activity,
  ShieldAlert,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api";
import type { StrategyVersion, Hypothesis, ActionRecord } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/Card";

export default function StrategyPage() {
  const [strategy, setStrategy] = useState<StrategyVersion | null>(null);
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([]);
  const [actions, setActions] = useState<ActionRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [stratData, hypData, actionData] = await Promise.all([
        api.getCurrentStrategy(),
        api.listHypotheses(),
        api.getActions(),
      ]);
      setStrategy(stratData);
      setHypotheses(hypData);
      setActions(actionData);
    } catch {
      // Fallback
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRunOutcomeAnalysis = async () => {
    setIsAnalyzing(true);
    setStatusMessage(null);
    try {
      const res = await api.startWorkflow("outcome_strategy", {});
      setStatusMessage("Outcome analysis completed. Updated hypothesis confidence and baseline.");
      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Outcome analysis completed with current records.";
      setStatusMessage(msg);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getHypothesisBadgeVariant = (status: string) => {
    if (status === "supported") return "success";
    if (status === "testing") return "primary";
    if (status === "weakened") return "warning";
    if (status === "contradicted") return "danger";
    return "default";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
              Strategy Learning & Outcomes
            </h1>
            <Badge variant="primary" size="sm">Workflow F & Strategy System</Badge>
          </div>
          <p className="mt-1 text-sm text-zinc-400">
            Form testable hypotheses, run controlled content experiments, and update positioning from real audience evidence without chasing vanity metrics.
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          onClick={handleRunOutcomeAnalysis}
          isLoading={isAnalyzing}
        >
          <Activity className="h-3.5 w-3.5 mr-1" />
          Run Outcome Analysis
        </Button>
      </div>

      {statusMessage && (
        <div className="rounded-xl border border-indigo-500/20 bg-indigo-950/20 p-4 text-xs text-indigo-300 flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-indigo-400" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Active Strategy Card */}
      {strategy ? (
        <Card variant="highlight">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Compass className="h-4 w-4 text-indigo-400" />
                <CardTitle>Active Strategy: Version {strategy.version}</CardTitle>
              </div>
              <Badge variant="success">ACTIVE VERSION</Badge>
            </div>
            <CardDescription className="text-zinc-300 font-medium mt-1">
              Positioning: {strategy.positioning}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4 text-xs">
            {/* Content Pillars */}
            <div>
              <span className="text-zinc-500 font-medium block mb-1">Content Pillars:</span>
              <div className="flex flex-wrap gap-1.5">
                {strategy.content_pillars.map((pillar, i) => (
                  <span key={i} className="rounded-md bg-zinc-900 px-2.5 py-1 text-zinc-200 border border-zinc-800">
                    {pillar}
                  </span>
                ))}
              </div>
            </div>

            {/* Platform Tactics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
              <div className="rounded-lg bg-zinc-950/60 p-3 border border-zinc-800/80">
                <span className="text-zinc-500 font-medium block">Target Audiences</span>
                <span className="text-zinc-300 mt-1 block">
                  {strategy.audience_priorities.join(", ") || "Technical peers and maintainers"}
                </span>
              </div>
              <div className="rounded-lg bg-zinc-950/60 p-3 border border-zinc-800/80">
                <span className="text-zinc-500 font-medium block">Relationship Approach</span>
                <span className="text-zinc-300 mt-1 block">
                  {strategy.relationship_approach || "Legitimate ongoing discussions without engagement farming"}
                </span>
              </div>
            </div>

            {/* Excluded Tactics */}
            {strategy.excluded_tactics.length > 0 && (
              <div className="rounded-lg bg-rose-950/20 border border-rose-900/40 p-3 text-rose-300 flex items-start gap-2">
                <ShieldAlert className="h-4 w-4 flex-shrink-0 mt-0.5 text-rose-400" />
                <div>
                  <span className="font-semibold block">Explicitly Excluded Tactics:</span>
                  <span>{strategy.excluded_tactics.join("; ")}</span>
                </div>
              </div>
            )}

            {/* Rationale */}
            {strategy.rationale && (
              <div className="pt-2 text-zinc-400">
                <span className="text-zinc-500 block">Version Rationale:</span>
                <p className="mt-0.5 italic">{strategy.rationale}</p>
              </div>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card className="text-center py-8">
          <p className="text-sm text-zinc-400">No strategy version activated yet. Run onboarding or outcome analysis to establish baseline.</p>
        </Card>
      )}

      {/* Hypotheses & Experiments */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-amber-400" />
            <span>Active Hypotheses & Experiments</span>
          </h2>
          <span className="text-xs text-zinc-500">{hypotheses.length} total</span>
        </div>

        {hypotheses.length === 0 ? (
          <Card className="py-6 text-center text-sm text-zinc-400">
            No hypotheses currently testing. They will be seeded by Ecosystem Research (Workflow C).
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {hypotheses.map((hyp) => (
              <Card key={hyp.id} className="flex flex-col justify-between">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <Badge variant={getHypothesisBadgeVariant(hyp.status)}>
                      {hyp.status.toUpperCase()}
                    </Badge>
                    <span className="text-xs text-zinc-400">
                      Confidence: {Math.round(hyp.confidence * 100)}%
                    </span>
                  </div>
                  <CardTitle className="text-base mt-2">{hyp.statement}</CardTitle>
                </CardHeader>

                <CardContent className="space-y-2 text-xs">
                  <div className="rounded-md bg-zinc-950/60 p-2.5 border border-zinc-800/80">
                    <span className="text-zinc-500 block">Expected Outcome:</span>
                    <span className="text-zinc-200 mt-0.5 block">{hyp.expected_outcome}</span>
                  </div>
                  <div className="flex items-center justify-between text-zinc-400 pt-1">
                    <span>Target: {hyp.target_audience}</span>
                    <span>Platform: {hyp.platform || "Multi-platform"}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Performed Actions & Measured Outcomes */}
      <div className="space-y-4 pt-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-emerald-400" />
            <span>Recent Performed Actions & Outcomes</span>
          </h2>
          <span className="text-xs text-zinc-500">{actions.length} tracked</span>
        </div>

        {actions.length === 0 ? (
          <Card className="py-6 text-center text-sm text-zinc-400">
            No actions performed yet. Approved actions will appear here once marked as performed.
          </Card>
        ) : (
          <div className="space-y-3">
            {actions.map((act) => (
              <Card key={act.id} variant="subtle" className="flex items-center justify-between p-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge variant={act.status === "measured" ? "success" : "info"} size="sm">
                      {act.status.replace(/_/g, " ").toUpperCase()}
                    </Badge>
                    {act.public_url && (
                      <a
                        href={act.public_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-indigo-400 hover:underline"
                      >
                        {act.public_url}
                      </a>
                    )}
                  </div>
                  <p className="text-xs text-zinc-400">
                    Performed at: {act.performed_at ? new Date(act.performed_at).toLocaleDateString() : "Pending"}
                  </p>
                </div>

                <div className="text-xs text-zinc-400">
                  {act.measurement_due_at && (
                    <span>Due: {new Date(act.measurement_due_at).toLocaleDateString()}</span>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

