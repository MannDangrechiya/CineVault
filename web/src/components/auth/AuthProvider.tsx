"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";

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

  const fetchCurrentUser = useCallback(async () => {
    try {
      setIsLoading(true);
      const res = await fetch("/api/auth/me", { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        if (data.authenticated && data.user) {
          setUser(data.user);
        } else {
          setUser(null);
        }
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  const login = (returnTo?: string) => {
    const target = returnTo ? `/api/auth/login?returnTo=${encodeURIComponent(returnTo)}` : "/api/auth/login";
    window.location.href = target;
  };

  const logout = () => {
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
