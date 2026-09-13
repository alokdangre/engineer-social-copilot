"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  Brain,
  Plus,
  Trash2,
  Link as LinkIcon,
  Search,
  CheckCircle,
  RefreshCw,
  AlertTriangle,
} from "lucide-react";
import { api } from "@/lib/api";
import type {
  MemoryRecord,
  MemoryCategory,
  EvidenceStatus,
  Visibility,
  MemoryCreate,
} from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/Card";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/Textarea";
import { Select } from "@/components/ui/Select";

const CATEGORIES: { value: string; label: string }[] = [
  { value: "all", label: "All Categories" },
  { value: "technical_knowledge", label: "Technical Knowledge" },
  { value: "projects_contributions", label: "Projects & Contributions" },
  { value: "reading_media", label: "Reading & Media" },
  { value: "events_experiences", label: "Events & Experiences" },
  { value: "opinions_reflections", label: "Opinions & Reflections" },
  { value: "people_relationships", label: "People & Relationships" },
  { value: "goals_audiences", label: "Goals & Audiences" },
  { value: "identity_preferences", label: "Identity & Preferences" },
  { value: "content_actions", label: "Content & Actions" },
  { value: "strategies_experiments", label: "Strategies & Experiments" },
];

export default function MemoryExplorerPage() {
  const [memories, setMemories] = useState<MemoryRecord[]>([]);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<string | null>(null);

  // Add Memory Modal
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [newCategory, setNewCategory] = useState<MemoryCategory>("technical_knowledge");
  const [newTitle, setNewTitle] = useState("");
  const [newStatement, setNewStatement] = useState("");
  const [newEvidenceStatus, setNewEvidenceStatus] = useState<EvidenceStatus>("user_confirmed");
  const [newVisibility, setNewVisibility] = useState<Visibility>("approved_public");
  const [newConfidence, setNewConfidence] = useState("0.9");

  // Link Memory Modal
  const [isLinkModalOpen, setIsLinkModalOpen] = useState(false);
  const [sourceMemoryId, setSourceMemoryId] = useState("");
  const [targetMemoryId, setTargetMemoryId] = useState("");
  const [linkRelation, setLinkRelation] = useState("supports");

  const showToast = (msg: string) => {
    setSuccessToast(msg);
    setTimeout(() => setSuccessToast(null), 3000);
  };

  const loadMemories = useCallback(async () => {
    setIsLoading(true);
    setErrorBanner(null);
    try {
      const categoryParam = selectedCategory === "all" ? undefined : selectedCategory;
      const data = await api.listMemories(categoryParam);
      setMemories(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load memories";
      setErrorBanner(msg);
    } finally {
      setIsLoading(false);
    }
  }, [selectedCategory]);

  useEffect(() => {
    loadMemories();
  }, [loadMemories]);

  const handleCreateMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: MemoryCreate = {
        category: newCategory,
        title: newTitle,
        statement: newStatement,
        evidence_status: newEvidenceStatus,
        visibility: newVisibility,
        confidence: parseFloat(newConfidence) || 0.9,
      };
      await api.createMemory(payload);
      setIsAddModalOpen(false);
      setNewTitle("");
      setNewStatement("");
      showToast("Memory created successfully.");
      await loadMemories();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create memory";
      setErrorBanner(msg);
    }
  };

  const handleDeleteMemory = async (id: string) => {
    try {
      await api.deleteMemory(id);
      setMemories((prev) => prev.filter((m) => m.id !== id));
      showToast("Memory deleted.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to delete memory";
      setErrorBanner(msg);
    }
  };

  const handleCreateLink = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourceMemoryId || !targetMemoryId) return;
    try {
      await api.createMemoryLink(sourceMemoryId, targetMemoryId, linkRelation);
      setIsLinkModalOpen(false);
      showToast("Memory relationship linked.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to link memories";
      setErrorBanner(msg);
    }
  };

  const filteredMemories = memories.filter((m) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      m.title.toLowerCase().includes(q) ||
      m.statement.toLowerCase().includes(q) ||
      m.category.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {successToast && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-3 text-sm font-medium text-white shadow-xl">
          <CheckCircle className="h-4 w-4" />
          <span>{successToast}</span>
        </div>
      )}

      {errorBanner && (
        <div className="flex items-center justify-between rounded-xl border border-rose-800 bg-rose-950/40 p-4 text-sm text-rose-200">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-rose-400" />
            <span>{errorBanner}</span>
          </div>
          <button onClick={() => setErrorBanner(null)} className="text-xs text-rose-400">
            Dismiss
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
              Personal Structured Memory
            </h1>
            <Badge variant="primary" size="sm">Workflow A & Memory Graph</Badge>
          </div>
          <p className="mt-1 text-sm text-zinc-400">
            Typed, linked records with provenance, confidence, and visibility. The agent retrieves focused memory packets instead of dumping raw history.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsLinkModalOpen(true)}
          >
            <LinkIcon className="h-3.5 w-3.5 mr-1" />
            Link Memories
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsAddModalOpen(true)}
          >
            <Plus className="h-3.5 w-3.5 mr-1" />
            Add Memory
          </Button>
        </div>
      </div>

      {/* Filter & Search Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto pb-2 sm:pb-0">
          <Select
            options={CATEGORIES}
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="w-56"
          />
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
          <Input
            placeholder="Search memories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* Memory Cards Grid */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-16 text-zinc-500">
          <RefreshCw className="h-8 w-8 animate-spin text-indigo-500 mb-3" />
          <p className="text-sm">Loading memories...</p>
        </div>
      ) : filteredMemories.length === 0 ? (
        <Card className="text-center py-12">
          <div className="max-w-md mx-auto space-y-3">
            <Brain className="mx-auto h-10 w-10 text-zinc-500" />
            <h3 className="text-base font-semibold text-zinc-100">No Memories Found</h3>
            <p className="text-sm text-zinc-400">
              {searchQuery
                ? "No memories matched your search query."
                : "No memories saved in this category yet."}
            </p>
            <div className="pt-2">
              <Button variant="primary" onClick={() => setIsAddModalOpen(true)}>
                Add First Memory
              </Button>
            </div>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredMemories.map((mem) => (
            <Card key={mem.id} className="flex flex-col justify-between hover:border-zinc-700 transition-colors">
              <CardHeader>
                <div className="flex items-center justify-between gap-2">
                  <Badge variant="primary">{mem.category.replace(/_/g, " ")}</Badge>
                  <div className="flex items-center gap-1.5">
                    <Badge variant={mem.visibility === "approved_public" ? "success" : "default"}>
                      {mem.visibility.replace(/_/g, " ")}
                    </Badge>
                    <Badge variant={mem.evidence_status === "user_confirmed" ? "info" : "warning"}>
                      {mem.evidence_status.replace(/_/g, " ")}
                    </Badge>
                  </div>
                </div>
                <CardTitle className="mt-2 text-base">{mem.title}</CardTitle>
              </CardHeader>

              <CardContent>
                <p className="text-xs text-zinc-300 font-mono leading-relaxed bg-zinc-950/60 p-3 rounded-lg border border-zinc-800/80 whitespace-pre-wrap">
                  {mem.statement}
                </p>
              </CardContent>

              <CardFooter className="text-xs text-zinc-500 justify-between">
                <div className="flex items-center gap-3">
                  <span>Confidence: {Math.round(mem.confidence * 100)}%</span>
                  <span>Platform: {mem.source_platform}</span>
                </div>
                <button
                  onClick={() => handleDeleteMemory(mem.id)}
                  className="text-zinc-500 hover:text-rose-400 transition-colors"
                  title="Delete memory"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {/* Add Memory Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Add Structured Memory Record"
        description="Explicitly record a technical capability, project milestone, opinion, or event."
      >
        <form onSubmit={handleCreateMemory} className="space-y-4">
          <Select
            label="Memory Category"
            value={newCategory}
            onChange={(e) => setNewCategory(e.target.value as MemoryCategory)}
            options={CATEGORIES.filter((c) => c.value !== "all")}
          />

          <Input
            label="Title / Concept Name"
            placeholder="e.g., PostgreSQL Row-Level Security Architecture"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            required
          />

          <Textarea
            label="Statement / Detailed Finding"
            placeholder="Detailed evidence or insight..."
            rows={4}
            value={newStatement}
            onChange={(e) => setNewStatement(e.target.value)}
            required
          />

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <Select
              label="Evidence Status"
              value={newEvidenceStatus}
              onChange={(e) => setNewEvidenceStatus(e.target.value as EvidenceStatus)}
              options={[
                { value: "user_confirmed", label: "User Confirmed" },
                { value: "observed", label: "Observed" },
                { value: "self_reported", label: "Self Reported" },
              ]}
            />
            <Select
              label="Visibility Scope"
              value={newVisibility}
              onChange={(e) => setNewVisibility(e.target.value as Visibility)}
              options={[
                { value: "approved_public", label: "Approved Public" },
                { value: "potentially_shareable", label: "Potentially Shareable" },
                { value: "private", label: "Private" },
              ]}
            />
            <Input
              label="Confidence (0-1)"
              type="number"
              step="0.05"
              min="0"
              max="1"
              value={newConfidence}
              onChange={(e) => setNewConfidence(e.target.value)}
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-zinc-800">
            <Button variant="ghost" type="button" onClick={() => setIsAddModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Save Memory
            </Button>
          </div>
        </form>
      </Modal>

      {/* Link Memories Modal */}
      <Modal
        isOpen={isLinkModalOpen}
        onClose={() => setIsLinkModalOpen(false)}
        title="Link Two Memory Records"
        description="Establish explicit relationships (e.g., a project contribution supports technical knowledge)."
      >
        <form onSubmit={handleCreateLink} className="space-y-4">
          <Select
            label="Source Memory"
            value={sourceMemoryId}
            onChange={(e) => setSourceMemoryId(e.target.value)}
            options={[
              { value: "", label: "Select Source Memory..." },
              ...memories.map((m) => ({ value: m.id, label: `[${m.category}] ${m.title}` })),
            ]}
          />

          <Select
            label="Relation Type"
            value={linkRelation}
            onChange={(e) => setLinkRelation(e.target.value)}
            options={[
              { value: "supports", label: "Supports / Backs up" },
              { value: "derived_from", label: "Derived From" },
              { value: "builds_upon", label: "Builds Upon" },
              { value: "contradicts", label: "Contradicts / Evolved From" },
            ]}
          />

          <Select
            label="Target Memory"
            value={targetMemoryId}
            onChange={(e) => setTargetMemoryId(e.target.value)}
            options={[
              { value: "", label: "Select Target Memory..." },
              ...memories.map((m) => ({ value: m.id, label: `[${m.category}] ${m.title}` })),
            ]}
          />

          <div className="flex justify-end gap-2 pt-3 border-t border-zinc-800">
            <Button variant="ghost" type="button" onClick={() => setIsLinkModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Create Link
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

