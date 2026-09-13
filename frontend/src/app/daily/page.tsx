"use client";

import React, { useState } from "react";
import {
  PenTool,
  Send,
  BookOpen,
  Code,
  CheckCircle,
  Lightbulb,
  AlertCircle,
  Shield,
} from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Textarea } from "@/components/ui/Textarea";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";

export default function DailyCapturePage() {
  const [reflection, setReflection] = useState("");
  const [evidenceLink, setEvidenceLink] = useState("");
  const [evidenceNote, setEvidenceNote] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [resultMessage, setResultMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [extractedMemories, setExtractedMemories] = useState<Array<{ title: string; category: string; statement: string }>>([]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reflection.trim()) {
      setErrorMessage("Please enter a reflection or learning update.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setResultMessage(null);

    try {
      const evidence = [];
      if (evidenceLink) {
        evidence.push({ type: "link", value: evidenceLink });
      }
      if (evidenceNote) {
        evidence.push({ type: "note", value: evidenceNote });
      }

      const res = await api.startWorkflow("daily_capture", {
        reflection,
        daily_text: reflection,
        evidence,
      });

      setResultMessage("Daily reflection successfully captured and classified into structured memory.");
      if (res.run.output_data?.memories) {
        setExtractedMemories(res.run.output_data.memories as any);
      } else {
        setExtractedMemories([
          {
            title: "Captured Experience",
            category: "technical_knowledge",
            statement: reflection,
          },
        ]);
      }
      setReflection("");
      setEvidenceLink("");
      setEvidenceNote("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to capture reflection";
      setErrorMessage(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Page Header */}
      <div className="border-b border-zinc-800 pb-5">
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
            Daily Work & Learning Capture
          </h1>
          <Badge variant="primary" size="sm">Workflow B</Badge>
        </div>
        <p className="mt-1 text-sm text-zinc-400">
          Capture authentic experiences that GitHub or public profiles cannot observe: struggles, decisions, book insights, and evolved opinions.
        </p>
      </div>

      {/* Prompts & Guardrails Banner */}
      <div className="rounded-xl border border-indigo-500/20 bg-indigo-950/20 p-4 text-xs text-zinc-300 space-y-2">
        <div className="flex items-center gap-2 font-medium text-indigo-300">
          <Lightbulb className="h-4 w-4" />
          <span>The Daily Reflection Prompt</span>
        </div>
        <p className="text-sm font-semibold text-zinc-100 italic">
          &ldquo;What useful happened today? Did you read, build, discuss, try, fail at, discover, or change your mind about anything?&rdquo;
        </p>
        <div className="flex items-center gap-1.5 text-zinc-400 pt-1">
          <Shield className="h-3.5 w-3.5 text-indigo-400" />
          <span>Preserves uncertainty and privacy. Reading a passage is never transformed into fabricated mastery.</span>
        </div>
      </div>

      {/* Form */}
      <Card>
        <form onSubmit={handleSubmit} className="space-y-5">
          <Textarea
            label="Today's Reflection or Work Experience"
            placeholder="Today I debugged an issue with database connection pools under high load, tried a new concurrency pattern, and realized..."
            rows={5}
            value={reflection}
            onChange={(e) => setReflection(e.target.value)}
            required
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Optional Supporting Link (PR, Docs, Article, Book)"
              placeholder="https://github.com/.../pull/42 or doc link"
              value={evidenceLink}
              onChange={(e) => setEvidenceLink(e.target.value)}
            />
            <Input
              label="Optional Evidence Context or Page Note"
              placeholder="e.g., Chapter 4 on Distributed Transactions"
              value={evidenceNote}
              onChange={(e) => setEvidenceNote(e.target.value)}
            />
          </div>

          {errorMessage && (
            <div className="flex items-center gap-2 text-xs text-rose-400 bg-rose-950/30 p-3 rounded-lg border border-rose-800">
              <AlertCircle className="h-4 w-4" />
              <span>{errorMessage}</span>
            </div>
          )}

          {resultMessage && (
            <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-950/30 p-3 rounded-lg border border-emerald-800">
              <CheckCircle className="h-4 w-4" />
              <span>{resultMessage}</span>
            </div>
          )}

          <div className="flex items-center justify-between pt-2">
            <div className="flex items-center gap-3 text-xs text-zinc-500">
              <span className="flex items-center gap-1">
                <BookOpen className="h-3.5 w-3.5" /> Reading
              </span>
              <span className="flex items-center gap-1">
                <Code className="h-3.5 w-3.5" /> Building
              </span>
              <span className="flex items-center gap-1">
                <PenTool className="h-3.5 w-3.5" /> Opinions
              </span>
            </div>

            <Button type="submit" variant="primary" isLoading={isSubmitting}>
              <Send className="h-3.5 w-3.5 mr-1" />
              Capture Daily Memory
            </Button>
          </div>
        </form>
      </Card>

      {/* Extracted Candidates Feedback */}
      {extractedMemories.length > 0 && (
        <div className="space-y-3 pt-4">
          <h2 className="text-base font-semibold text-zinc-100 flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-emerald-400" />
            <span>Synthesized Memory Records</span>
          </h2>
          <div className="grid grid-cols-1 gap-3">
            {extractedMemories.map((mem, idx) => (
              <Card key={idx} variant="subtle">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm">{mem.title || "Daily Memory Item"}</CardTitle>
                    <Badge variant="primary">{mem.category}</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-zinc-300 font-mono leading-relaxed">{mem.statement}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

