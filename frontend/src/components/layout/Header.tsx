"use client";

import React, { useEffect, useState } from "react";
import { Sparkles, Activity, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";

export const Header: React.FC<{ onRunCycle?: () => void }> = ({ onRunCycle }) => {
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    const check = async () => {
      try {
        const res = await api.getHealth();
        if (res.status === "ok") {
          setBackendStatus("online");
        } else {
          setBackendStatus("offline");
        }
      } catch {
        setBackendStatus("offline");
      }
    };
    check();
    const interval = setInterval(check, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-zinc-800 bg-zinc-950/80 px-6 backdrop-blur-md">
      {/* Title & Badge */}
      <div className="flex items-center gap-3">
        <h1 className="text-base font-semibold text-zinc-100 flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-indigo-400" />
          <span>AI Social Media & Career Manager</span>
        </h1>
        <span className="hidden sm:inline-flex items-center gap-1 rounded-full bg-indigo-950/80 px-2.5 py-0.5 text-xs font-medium text-indigo-300 border border-indigo-700/50">
          <ShieldCheck className="h-3 w-3 text-indigo-400" />
          Human-Reviewed
        </span>
      </div>

      {/* Status & Actions */}
      <div className="flex items-center gap-4">
        {/* Backend health pill */}
        <div className="flex items-center gap-2 rounded-full border border-zinc-800 bg-zinc-900/60 px-3 py-1 text-xs text-zinc-400">
          <span
            className={`h-2 w-2 rounded-full ${
              backendStatus === "online"
                ? "bg-emerald-500 shadow-sm shadow-emerald-500/50"
                : backendStatus === "offline"
                ? "bg-rose-500"
                : "bg-amber-500 animate-pulse"
            }`}
          />
          <span className="hidden md:inline">
            {backendStatus === "online"
              ? "FastAPI & Database Online"
              : backendStatus === "offline"
              ? "Backend Offline"
              : "Checking API..."}
          </span>
        </div>

        {onRunCycle && (
          <Button
            size="sm"
            variant="primary"
            onClick={onRunCycle}
            className="hidden sm:inline-flex"
          >
            <Activity className="h-3.5 w-3.5 mr-1" />
            Generate Daily Recommendations
          </Button>
        )}
      </div>
    </header>
  );
};

