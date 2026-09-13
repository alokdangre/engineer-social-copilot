"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  Target,
  Clock,
  Play,
  Plus,
  CheckCircle,
  AlertCircle,
  KeyRound,
  Trash2,
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/auth/AuthProvider";
import type {
  Goal,
  GoalCreate,
  LLMCredentialStatus,
  LLMProvider,
  SchedulerStatus,
} from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Textarea } from "@/components/ui/Textarea";

export default function SettingsPage() {
  const { refreshLLMCredential } = useAuth();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null);
  const [llmCredential, setLLMCredential] = useState<LLMCredentialStatus | null>(null);
  const [llmProvider, setLLMProvider] = useState<LLMProvider>("gemini");
  const [llmApiKey, setLLMApiKey] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isRunningJob, setIsRunningJob] = useState(false);
  const [isSavingLLM, setIsSavingLLM] = useState(false);

  // Add Goal modal
  const [isGoalModalOpen, setIsGoalModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newAudiences, setNewAudiences] = useState("");
  const [newPriority, setNewPriority] = useState("60");

  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const [goalsData, schedData, credentialData] = await Promise.all([
        api.listGoals(),
        api.getSchedulerStatus(),
        api.getLLMCredential(),
      ]);
      setGoals(goalsData);
      setSchedulerStatus(schedData);
      setLLMCredential(credentialData);
      if (credentialData.provider) {
        setLLMProvider(credentialData.provider);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load settings data";
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreateGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: GoalCreate = {
        title: newTitle,
        description: newDescription,
        target_audiences: newAudiences
          ? newAudiences.split(",").map((a) => a.trim()).filter(Boolean)
          : [],
        priority: parseInt(newPriority, 10) || 50,
      };
      await api.createGoal(payload);
      setIsGoalModalOpen(false);
      setNewTitle("");
      setNewDescription("");
      setNewAudiences("");
      showToast("Career goal created.");
      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create goal";
      setErrorMessage(msg);
    }
  };

  const handleTriggerScheduler = async () => {
    setIsRunningJob(true);
    try {
      await api.runScheduler();
      showToast("Background jobs completed: retention purged, measurements checked.");
      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to trigger scheduler";
      setErrorMessage(msg);
    } finally {
      setIsRunningJob(false);
    }
  };

  const handleSaveLLM = async (event: React.FormEvent) => {
    event.preventDefault();
    if (llmApiKey.trim().length < 10) {
      setErrorMessage("Enter a valid API key (at least 10 characters).");
      return;
    }

    setIsSavingLLM(true);
    setErrorMessage(null);
    try {
      const credential = await api.saveLLMCredential(llmProvider, llmApiKey.trim());
      setLLMCredential(credential);
      setLLMApiKey("");
      await refreshLLMCredential();
      showToast("Your LLM API key was encrypted and saved.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save the API key";
      setErrorMessage(msg);
    } finally {
      setIsSavingLLM(false);
    }
  };

  const handleDeleteLLM = async () => {
    setIsSavingLLM(true);
    setErrorMessage(null);
    try {
      await api.deleteLLMCredential();
      setLLMCredential({
        configured: false,
        provider: null,
        key_hint: null,
        updated_at: null,
      });
      setLLMApiKey("");
      await refreshLLMCredential();
      showToast("Your LLM API key was removed.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to remove the API key";
      setErrorMessage(msg);
    } finally {
      setIsSavingLLM(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Toast Alert */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-3 text-sm font-medium text-white shadow-xl">
          <CheckCircle className="h-4 w-4" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Error Alert */}
      {errorMessage && (
        <div className="flex items-center justify-between rounded-xl border border-rose-800 bg-rose-950/40 p-4 text-sm text-rose-200">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-rose-400" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-xs text-rose-400">
            Dismiss
          </button>
        </div>
      )}

      {/* Header */}
      <div className="border-b border-zinc-800 pb-5">
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
            Account Settings
          </h1>
          <Badge variant="primary" size="sm">System Configuration</Badge>
        </div>
        <p className="mt-1 text-sm text-zinc-400">
          Add your own AI provider key, manage goals, and monitor background tasks.
        </p>
      </div>

      <Card className="border-indigo-800/70 bg-indigo-950/20">
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <CardTitle className="flex items-center gap-2">
                <KeyRound className="h-4 w-4 text-indigo-400" />
                Your LLM API key
              </CardTitle>
              <CardDescription className="mt-1">
                Required for personalized analysis, research, recommendations, and embeddings.
              </CardDescription>
            </div>
            <Badge variant={llmCredential?.configured ? "success" : "warning"}>
              {llmCredential?.configured ? "Configured" : "Action required"}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSaveLLM} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-[180px_1fr]">
              <Select
                label="Provider"
                value={llmProvider}
                onChange={(event) => setLLMProvider(event.target.value as LLMProvider)}
                options={[
                  { value: "gemini", label: "Google Gemini" },
                  { value: "openai", label: "OpenAI" },
                ]}
                disabled={isLoading || isSavingLLM}
              />
              <Input
                label={llmCredential?.configured ? "Replace API key" : "API key"}
                type="password"
                value={llmApiKey}
                onChange={(event) => setLLMApiKey(event.target.value)}
                placeholder={
                  llmCredential?.configured && llmCredential.key_hint
                    ? `Current key ends in ${llmCredential.key_hint}`
                    : llmProvider === "gemini"
                      ? "Paste your Google AI Studio API key"
                      : "Paste your OpenAI API key"
                }
                helperText="The full key is never returned after you save it."
                autoComplete="off"
                disabled={isLoading || isSavingLLM}
                required
              />
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-zinc-800 pt-4">
              <p className="max-w-xl text-xs leading-5 text-zinc-400">
                The key is encrypted with the server secret and used only for your workflows.
                Provider usage is billed directly to your own account.
              </p>
              <div className="flex items-center gap-2">
                {llmCredential?.configured ? (
                  <Button
                    type="button"
                    variant="danger"
                    size="sm"
                    onClick={handleDeleteLLM}
                    disabled={isSavingLLM}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Remove
                  </Button>
                ) : null}
                <Button
                  type="submit"
                  size="sm"
                  isLoading={isSavingLLM}
                  disabled={isLoading || llmApiKey.trim().length < 10}
                >
                  {llmCredential?.configured ? "Replace key" : "Save key"}
                </Button>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Career Goals Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
              <Target className="h-4 w-4 text-indigo-400" />
              <span>Career & Technical Goals</span>
            </h2>
            <p className="text-xs text-zinc-400">
              Workflows prioritize recommendations and research that directly align with these objectives.
            </p>
          </div>

          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsGoalModalOpen(true)}
          >
            <Plus className="h-3.5 w-3.5 mr-1" />
            Add Goal
          </Button>
        </div>

        {goals.length === 0 ? (
          <Card className="py-8 text-center text-sm text-zinc-400">
            No active goals recorded yet. Add your first goal to guide recommendations.
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-3">
            {goals.map((g) => (
              <Card key={g.id} variant="subtle">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{g.title}</CardTitle>
                    <Badge variant="primary">Priority: {g.priority}/100</Badge>
                  </div>
                  <CardDescription className="text-zinc-300 mt-1">
                    {g.description}
                  </CardDescription>
                </CardHeader>
                {g.target_audiences.length > 0 && (
                  <CardContent>
                    <div className="flex items-center gap-2 text-xs text-zinc-400">
                      <span className="text-zinc-500">Target Audiences:</span>
                      <div className="flex flex-wrap gap-1">
                        {g.target_audiences.map((aud, i) => (
                          <span key={i} className="rounded bg-zinc-800 px-2 py-0.5 text-zinc-300 text-[11px]">
                            {aud}
                          </span>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Background Scheduler Section */}
      <div className="space-y-4 pt-6 border-t border-zinc-800">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
              <Clock className="h-4 w-4 text-emerald-400" />
              <span>Background Maintenance Scheduler</span>
            </h2>
            <p className="text-xs text-zinc-400">
              Automates LinkedIn 48-hour retention purge, recommendation expiration, and 24h outcome measurements.
            </p>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={handleTriggerScheduler}
            isLoading={isRunningJob}
          >
            <Play className="h-3.5 w-3.5 mr-1" />
            Run All Due Jobs Now
          </Button>
        </div>

        <Card variant="subtle">
          <CardContent className="pt-4 space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-zinc-400">Scheduler Daemon Status:</span>
              <Badge variant={schedulerStatus?.is_running ? "success" : "default"}>
                {schedulerStatus?.is_running ? "ACTIVE / RUNNING" : "STOPPED / MANUAL"}
              </Badge>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-zinc-400">Check Interval:</span>
              <span className="text-zinc-200 font-mono">
                {schedulerStatus?.interval_seconds || 300} seconds
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-zinc-400">Last Execution Time:</span>
              <span className="text-zinc-200 font-mono">
                {schedulerStatus?.last_run_at
                  ? new Date(schedulerStatus.last_run_at).toLocaleString()
                  : "Never (Ready)"}
              </span>
            </div>

            <div className="rounded-md bg-zinc-950/60 p-3 border border-zinc-800/80 text-[11px] text-zinc-400 space-y-1">
              <span className="font-semibold text-zinc-300 block">Scheduled Subsystems:</span>
              <ul className="list-disc list-inside space-y-0.5">
                <li>Purge expired third-party platform content (LinkedIn 48h limit)</li>
                <li>Soft-delete expired temporary reading notes & memories</li>
                <li>Expire unreviewed time-sensitive recommendations</li>
                <li>Transition performed actions to measurement scheduled at 24h</li>
                <li>Flag expired connector OAuth tokens</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Add Goal Modal */}
      <Modal
        isOpen={isGoalModalOpen}
        onClose={() => setIsGoalModalOpen(false)}
        title="Add Career or Technical Goal"
        description="Define a goal to prioritize recommendations and ecosystem research."
      >
        <form onSubmit={handleCreateGoal} className="space-y-4">
          <Input
            label="Goal Title"
            placeholder="e.g., Gain visibility in open source DevRel and systems programming"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            required
          />

          <Textarea
            label="Description & Intended Impact"
            placeholder="What specific skills, connections, or project visibility do you want to build?"
            rows={3}
            value={newDescription}
            onChange={(e) => setNewDescription(e.target.value)}
            required
          />

          <Input
            label="Target Audiences (Comma-separated)"
            placeholder="e.g., Open Source Maintainers, DevRel Managers, Infrastructure Founders"
            value={newAudiences}
            onChange={(e) => setNewAudiences(e.target.value)}
          />

          <Input
            label="Priority (0-100)"
            type="number"
            min="0"
            max="100"
            value={newPriority}
            onChange={(e) => setNewPriority(e.target.value)}
          />

          <div className="flex justify-end gap-2 pt-3 border-t border-zinc-800">
            <Button variant="ghost" type="button" onClick={() => setIsGoalModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Save Goal
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
