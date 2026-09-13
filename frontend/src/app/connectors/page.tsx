"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  Share2,
  CheckCircle,
  RefreshCw,
  Shield,
  Key,
  ExternalLink,
  Clock,
  AlertTriangle,
  Github,
  Twitter,
  Linkedin,
} from "lucide-react";
import { api } from "@/lib/api";
import type { ConnectorAccount } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/Card";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";

export default function ConnectorsPage() {
  const [connectors, setConnectors] = useState<ConnectorAccount[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [syncingPlatform, setSyncingPlatform] = useState<string | null>(null);

  // Manual token modal
  const [tokenModalPlatform, setTokenModalPlatform] = useState<string | null>(null);
  const [manualToken, setManualToken] = useState("");
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const loadConnectors = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await api.listConnectors();
      setConnectors(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load connectors";
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConnectors();
  }, [loadConnectors]);

  const handleSync = async (platform: string) => {
    setSyncingPlatform(platform);
    try {
      const res = await api.syncConnector(platform);
      showToast(`Synced ${platform.toUpperCase()}: ${res.created} new items, ${res.updated} updated.`);
      await loadConnectors();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : `Failed to sync ${platform}`;
      setErrorMessage(msg);
    } finally {
      setSyncingPlatform(null);
    }
  };

  const handleSaveToken = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tokenModalPlatform || !manualToken) return;

    try {
      await api.saveConnectorToken(tokenModalPlatform, manualToken);
      showToast(`Saved token for ${tokenModalPlatform.toUpperCase()}. Connected successfully.`);
      setTokenModalPlatform(null);
      setManualToken("");
      await loadConnectors();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to connect token";
      setErrorMessage(msg);
    }
  };

  const platforms = [
    {
      id: "github",
      name: "GitHub",
      icon: Github,
      description: "Evidence of technical work: repositories, pull requests, commits, and languages.",
      role: "Source of Technical Truth",
      retentionNote: "Retained permanently as personal project history.",
    },
    {
      id: "x",
      name: "X (Twitter)",
      icon: Twitter,
      description: "Technical conversation and discovery: short-form posts, threads, replies, and visible metrics.",
      role: "Ecosystem Conversation",
      retentionNote: "Operational metrics and post history. No AI model training.",
    },
    {
      id: "linkedin",
      name: "LinkedIn",
      icon: Linkedin,
      description: "Professional reputation and career positioning: articles, posts, and member engagement.",
      role: "Professional Distribution",
      retentionNote: "Strict 48-hour conservative retention enforced on member content.",
    },
  ];

  return (
    <div className="space-y-6">
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
            <AlertTriangle className="h-4 w-4 text-rose-400" />
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
            Connected Accounts & Platform Boundaries
          </h1>
          <Badge variant="primary" size="sm">Platform Boundaries</Badge>
        </div>
        <p className="mt-1 text-sm text-zinc-400">
          Official API connectors with strict data privacy boundaries. Real connector implementations with mocked verification when credentials are not present.
        </p>
      </div>

      {/* Security Principles Banner */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4 text-xs text-zinc-300 space-y-2">
        <div className="flex items-center gap-2 font-medium text-zinc-200">
          <Shield className="h-4 w-4 text-indigo-400" />
          <span>Platform Privacy & Execution Principles</span>
        </div>
        <ul className="list-disc list-inside space-y-1 text-zinc-400">
          <li><strong>Zero Browser Automation:</strong> The product never scrapes or drives social websites with bots.</li>
          <li><strong>Human Execution:</strong> The agent suggests and drafts; you review and manually publish.</li>
          <li><strong>Conservative Retention:</strong> Third-party platform data follows strict retention rules (e.g. 48-hour LinkedIn purge).</li>
        </ul>
      </div>

      {/* Platform Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {platforms.map((p) => {
          const Icon = p.icon;
          const account = connectors.find((c) => c.platform === p.id);
          const isConnected = account && account.status === "connected";
          const isExpired = account && account.status === "expired";

          return (
            <Card key={p.id} className="flex flex-col justify-between">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-800 text-zinc-100">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <CardTitle className="text-base">{p.name}</CardTitle>
                      <span className="text-[11px] text-zinc-500">{p.role}</span>
                    </div>
                  </div>
                  <Badge
                    variant={
                      isConnected
                        ? "success"
                        : isExpired
                        ? "warning"
                        : "default"
                    }
                    size="sm"
                  >
                    {account ? account.status.toUpperCase() : "NOT CONNECTED"}
                  </Badge>
                </div>
                <CardDescription className="mt-2 text-xs leading-relaxed">
                  {p.description}
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-3 text-xs">
                {account?.username && (
                  <div className="rounded-md bg-zinc-950 p-2 border border-zinc-800/80">
                    <span className="text-zinc-500 block">Connected As:</span>
                    <span className="text-zinc-200 font-mono">@{account.username}</span>
                  </div>
                )}

                {/* Retention notice */}
                <div className="rounded-md bg-zinc-950/60 p-2.5 border border-zinc-800/60 text-[11px] text-zinc-400 flex items-start gap-1.5">
                  <Clock className="h-3.5 w-3.5 text-zinc-500 flex-shrink-0 mt-0.5" />
                  <span>{p.retentionNote}</span>
                </div>
              </CardContent>

              <CardFooter className="flex-col gap-2 pt-3">
                <div className="flex items-center justify-between w-full gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => {
                      setTokenModalPlatform(p.id);
                      setManualToken("");
                    }}
                  >
                    <Key className="h-3.5 w-3.5 mr-1" />
                    Set Token
                  </Button>

                  <Button
                    variant="primary"
                    size="sm"
                    className="flex-1"
                    disabled={!isConnected}
                    isLoading={syncingPlatform === p.id}
                    onClick={() => handleSync(p.id)}
                  >
                    <RefreshCw className="h-3.5 w-3.5 mr-1" />
                    Sync
                  </Button>
                </div>
              </CardFooter>
            </Card>
          );
        })}
      </div>

      {/* Manual Token Modal */}
      <Modal
        isOpen={Boolean(tokenModalPlatform)}
        onClose={() => setTokenModalPlatform(null)}
        title={`Configure ${tokenModalPlatform?.toUpperCase()} Access Token`}
        description="Enter a personal access token or test token. All tokens are encrypted at rest with Fernet cryptography."
      >
        <form onSubmit={handleSaveToken} className="space-y-4">
          <Input
            label="Access Token / Secret"
            type="password"
            placeholder="Paste access token here..."
            value={manualToken}
            onChange={(e) => setManualToken(e.target.value)}
            required
          />

          <p className="text-xs text-zinc-500">
            Tokens are encrypted using the application secret key before storage. They are never sent to third-party services.
          </p>

          <div className="flex justify-end gap-2 pt-3 border-t border-zinc-800">
            <Button variant="ghost" type="button" onClick={() => setTokenModalPlatform(null)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Connect Account
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

