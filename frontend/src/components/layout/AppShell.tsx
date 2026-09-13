"use client";

import React from "react";
import Link from "next/link";
import { KeyRound } from "lucide-react";
import { AuthProvider, useAuth } from "@/components/auth/AuthProvider";
import { AuthScreen } from "@/components/auth/AuthScreen";
import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";

function AuthenticatedApp({ children }: { children: React.ReactNode }) {
  const { user, llmCredential, isLoading, logout } = useAuth();

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-zinc-950 text-sm text-zinc-400">
        Checking your session…
      </main>
    );
  }

  if (user === null) {
    return <AuthScreen />;
  }

  return (
    <div className="flex min-h-screen flex-col bg-zinc-950 text-zinc-100">
      <Header user={user} onLogout={logout} />
      {llmCredential?.configured === false ? (
        <div className="border-b border-amber-800/70 bg-amber-950/40 px-6 py-2.5 text-sm text-amber-100">
          <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-center gap-x-2 gap-y-1">
            <KeyRound className="h-4 w-4 text-amber-400" />
            <span>Add your own Gemini or OpenAI API key before running AI workflows.</span>
            <Link
              href="/settings"
              className="font-semibold text-amber-300 underline underline-offset-4 hover:text-amber-200"
            >
              Open Settings
            </Link>
          </div>
        </div>
      ) : null}
      <div className="flex flex-1">
        <Sidebar />
        <main className="mx-auto w-full max-w-7xl flex-1 overflow-y-auto p-6 md:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <AuthenticatedApp>{children}</AuthenticatedApp>
    </AuthProvider>
  );
}
