"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  CheckSquare,
  PenTool,
  Brain,
  Target,
  Share2,
  Settings,
  Layers,
} from "lucide-react";

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  const navItems = [
    {
      name: "Daily Brief & Review",
      href: "/",
      icon: CheckSquare,
      description: "Workflows D & E: Recommendations & Review",
    },
    {
      name: "Daily Capture",
      href: "/daily",
      icon: PenTool,
      description: "Workflow B: Reflection & Work Ingestion",
    },
    {
      name: "Personal Memory",
      href: "/memory",
      icon: Brain,
      description: "Workflow A & 10-Category Memory Store",
    },
    {
      name: "Strategy & Outcomes",
      href: "/strategy",
      icon: Target,
      description: "Workflow F: Hypotheses & Experiments",
    },
    {
      name: "Connected Accounts",
      href: "/connectors",
      icon: Share2,
      description: "GitHub, X, LinkedIn & Retention",
    },
    {
      name: "Goals & Settings",
      href: "/settings",
      icon: Settings,
      description: "Career Goals & Background Jobs",
    },
  ];

  return (
    <aside className="w-64 flex-shrink-0 border-r border-zinc-800 bg-zinc-950 flex flex-col justify-between p-4 h-[calc(100vh-4rem)] sticky top-16">
      <div className="space-y-6">
        {/* Navigation list */}
        <nav className="space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all ${
                  isActive
                    ? "bg-indigo-600/15 text-indigo-400 border border-indigo-500/20"
                    : "text-zinc-400 hover:bg-zinc-900/80 hover:text-zinc-200"
                }`}
              >
                <Icon
                  className={`h-4 w-4 flex-shrink-0 transition-colors ${
                    isActive ? "text-indigo-400" : "text-zinc-500 group-hover:text-zinc-300"
                  }`}
                />
                <div className="flex flex-col">
                  <span>{item.name}</span>
                </div>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer / System summary */}
      <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/40 p-3">
        <div className="flex items-center gap-2 text-xs font-medium text-zinc-300">
          <Layers className="h-3.5 w-3.5 text-indigo-400" />
          <span>Workflows A–F Active</span>
        </div>
        <p className="mt-1 text-[11px] text-zinc-500 leading-relaxed">
          Stateful LangGraph runtime with human verification gates.
        </p>
      </div>
    </aside>
  );
};

