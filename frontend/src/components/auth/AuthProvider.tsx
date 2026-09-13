"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { api } from "@/lib/api";
import type { LLMCredentialStatus, UserAccount } from "@/lib/types";

interface AuthContextValue {
  user: UserAccount | null;
  llmCredential: LLMCredentialStatus | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, displayName: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshLLMCredential: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserAccount | null>(null);
  const [llmCredential, setLLMCredential] = useState<LLMCredentialStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshLLMCredential = useCallback(async () => {
    try {
      setLLMCredential(await api.getLLMCredential());
    } catch {
      setLLMCredential(null);
    }
  }, []);

  useEffect(() => {
    let isActive = true;

    Promise.all([
      api.getCurrentUser(),
      api.getLLMCredential().catch(() => null),
    ])
      .then(([currentUser, credential]) => {
        if (isActive) {
          setUser(currentUser);
          setLLMCredential(credential);
        }
      })
      .catch(() => {
        if (isActive) {
          setUser(null);
          setLLMCredential(null);
        }
      })
      .finally(() => {
        if (isActive) setIsLoading(false);
      });

    return () => {
      isActive = false;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    await api.login(email, password);
    const [currentUser, credential] = await Promise.all([
      api.getCurrentUser(),
      api.getLLMCredential().catch(() => null),
    ]);
    setUser(currentUser);
    setLLMCredential(credential);
  }, []);

  const register = useCallback(
    async (email: string, displayName: string, password: string) => {
      await api.register(email, displayName, password);
      await login(email, password);
    },
    [login]
  );

  const logout = useCallback(async () => {
    await api.logout();
    setUser(null);
    setLLMCredential(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      llmCredential,
      isLoading,
      login,
      register,
      logout,
      refreshLLMCredential,
    }),
    [
      user,
      llmCredential,
      isLoading,
      login,
      register,
      logout,
      refreshLLMCredential,
    ]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
