"use client";

import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";

export interface AuthUser {
  sub: string;
  email?: string;
  username?: string;
  roles: string[];
}

interface AuthContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (returnTo?: string) => void;
  logout: () => void;
  refetch: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  login: () => {},
  logout: () => {},
  refetch: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const queryClient = useQueryClient();
  const prevUserSubRef = useRef<string | null>(null);

  const fetchCurrentUser = useCallback(async () => {
    try {
      setIsLoading(true);
      const res = await fetch("/api/auth/me", { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        if (data.authenticated && data.user) {
          const newUser = data.user;
          if (prevUserSubRef.current && prevUserSubRef.current !== newUser.sub) {
            queryClient.clear();
          }
          prevUserSubRef.current = newUser.sub;
          setUser(newUser);
        } else {
          if (prevUserSubRef.current) {
            queryClient.clear();
          }
          prevUserSubRef.current = null;
          setUser(null);
        }
      } else {
        if (prevUserSubRef.current) {
          queryClient.clear();
        }
        prevUserSubRef.current = null;
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, [queryClient]);

  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  const login = (returnTo?: string) => {
    queryClient.clear();
    const target = returnTo ? `/api/auth/login?returnTo=${encodeURIComponent(returnTo)}` : "/api/auth/login";
    window.location.href = target;
  };

  const logout = () => {
    queryClient.clear();
    window.location.href = "/api/auth/logout";
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        refetch: fetchCurrentUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
