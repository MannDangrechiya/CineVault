"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  Clapperboard,
  Lock,
  ArrowLeft,
  Shield,
  AlertTriangle,
  Sparkles,
  User,
  ShieldCheck,
  KeyRound,
  CheckCircle2,
  ChevronDown,
  Loader2,
} from "lucide-react";

function LoginContent() {
  const searchParams = useSearchParams();
  const errorParam = searchParams.get("error");
  const isLoggedOut = searchParams.get("logged_out") === "1";
  const returnTo = searchParams.get("returnTo") || "/dashboard";

  const [email, setEmail] = useState("dev@cinevault.local");
  const [password, setPassword] = useState("devpass");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(errorParam || "");
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleLocalSignIn = async (
    targetEmail?: string,
    targetPassword?: string,
    role: "dev_user" | "curator" | "admin" = "dev_user"
  ) => {
    setIsLoading(true);
    setErrorMessage("");

    try {
      const res = await fetch("/api/auth/local-login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: targetEmail || email,
          password: targetPassword || password,
          role,
          returnTo,
        }),
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        setErrorMessage(data.error || "Authentication failed. Please check your credentials.");
        setIsLoading(false);
        return;
      }

      // Hard redirect to returnTo so Next.js middleware and client refresh session cleanly
      window.location.href = data.redirectUrl || returnTo;
    } catch {
      setErrorMessage("Unable to connect to authentication service.");
      setIsLoading(false);
    }
  };

  const handleKeycloakLogin = () => {
    window.location.href = `/api/auth/login?returnTo=${encodeURIComponent(returnTo)}`;
  };

  return (
    <div className="w-full max-w-md p-6 sm:p-8 rounded-3xl bg-zinc-900/90 border border-zinc-800 shadow-2xl shadow-violet-950/20 backdrop-blur-2xl space-y-6">
      {/* Brand Header */}
      <div className="flex flex-col items-center text-center space-y-2">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-violet-600/30 mb-1">
          <Clapperboard className="w-6 h-6 text-white" />
        </div>
        <h1 className="text-xl font-bold tracking-tight text-zinc-50">
          Sign In to <span className="text-violet-400">CineVault OS</span>
        </h1>
        <p className="text-xs text-zinc-400 max-w-xs leading-relaxed">
          Access your personal media library, neural recommendations, and social inbox.
        </p>
      </div>

      {/* Notifications */}
      {isLoggedOut && !errorMessage && (
        <div className="p-3 rounded-2xl bg-emerald-950/40 border border-emerald-800/60 text-xs text-emerald-300 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>You have been securely signed out.</span>
        </div>
      )}

      {errorMessage && (
        <div className="p-3.5 rounded-2xl bg-red-950/40 border border-red-800/60 text-xs text-red-300 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold text-red-200">Authentication Alert</div>
            <div className="text-[11px] text-red-300/80 mt-0.5">{errorMessage}</div>
          </div>
        </div>
      )}

      {/* PRIMARY: 1-Click Instant Demo Login Profiles */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between px-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-violet-400" />
            Quick One-Click Sign In
          </span>
          <span className="text-[10px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full font-mono">
            Instant Access
          </span>
        </div>

        <button
          onClick={() => handleLocalSignIn("dev@cinevault.local", "devpass", "dev_user")}
          disabled={isLoading}
          className="w-full p-3 rounded-2xl bg-violet-600 hover:bg-violet-500 border border-violet-500 text-white flex items-center justify-between shadow-lg shadow-violet-600/30 transition-all hover:scale-[1.02] active:scale-[0.99] cursor-pointer disabled:opacity-50"
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-white/20 flex items-center justify-center">
              <User className="w-4 h-4 text-white" />
            </div>
            <div className="text-left">
              <div className="text-xs font-bold">Sign In as Dev User</div>
              <div className="text-[10px] text-violet-200">dev@cinevault.local • Full Access</div>
            </div>
          </div>
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin text-white" />
          ) : (
            <span className="text-xs font-semibold px-2 py-0.5 bg-white/15 rounded-lg">Enter →</span>
          )}
        </button>

        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => handleLocalSignIn("curator@cinevault.local", "curatorpass", "curator")}
            disabled={isLoading}
            className="p-2.5 rounded-xl bg-zinc-950/80 hover:bg-zinc-800 border border-zinc-800 hover:border-zinc-700 text-left transition-all text-xs font-medium text-zinc-300 hover:text-white flex items-center gap-2 cursor-pointer disabled:opacity-50"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <div className="truncate">
              <div className="font-semibold text-zinc-200 truncate">Curator Profile</div>
              <div className="text-[10px] text-zinc-500 truncate">curator@cinevault</div>
            </div>
          </button>

          <button
            onClick={() => handleLocalSignIn("admin@cinevault.local", "adminpass", "admin")}
            disabled={isLoading}
            className="p-2.5 rounded-xl bg-zinc-950/80 hover:bg-zinc-800 border border-zinc-800 hover:border-zinc-700 text-left transition-all text-xs font-medium text-zinc-300 hover:text-white flex items-center gap-2 cursor-pointer disabled:opacity-50"
          >
            <KeyRound className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <div className="truncate">
              <div className="font-semibold text-zinc-200 truncate">System Admin</div>
              <div className="text-[10px] text-zinc-500 truncate">admin@cinevault</div>
            </div>
          </button>
        </div>
      </div>

      {/* SECONDARY: Direct Email & Password Form */}
      <div className="space-y-4 pt-3 border-t border-zinc-800/80">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleLocalSignIn();
          }}
          className="space-y-3"
        >
          <div>
            <label className="block text-[11px] font-medium text-zinc-400 mb-1">
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@cinevault.local"
              className="w-full px-3.5 py-2 text-xs bg-zinc-950 border border-zinc-800 rounded-xl text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-violet-500 transition-colors"
            />
          </div>

          <div>
            <label className="block text-[11px] font-medium text-zinc-400 mb-1">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3.5 py-2 text-xs bg-zinc-950 border border-zinc-800 rounded-xl text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-violet-500 transition-colors"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 px-4 text-xs font-semibold text-zinc-200 bg-zinc-800 hover:bg-zinc-700 hover:text-white border border-zinc-700 rounded-xl transition-all cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Lock className="w-3.5 h-3.5" />
            <span>Sign In with Credentials</span>
          </button>
        </form>
      </div>

      {/* TERTIARY: Enterprise OIDC Accordion */}
      <div className="pt-2">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="w-full flex items-center justify-between text-[11px] text-zinc-500 hover:text-zinc-300 py-1 transition-colors"
        >
          <span className="flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-zinc-500" />
            <span>Enterprise Keycloak OIDC (PKCE S256)</span>
          </span>
          <ChevronDown
            className={`w-3.5 h-3.5 transition-transform ${showAdvanced ? "rotate-180" : ""}`}
          />
        </button>

        {showAdvanced && (
          <div className="mt-3 p-3 rounded-xl bg-zinc-950/60 border border-zinc-850 space-y-2">
            <p className="text-[10px] text-zinc-400 leading-relaxed">
              Use when running against a centralized Keycloak identity provider on port 8080.
            </p>
            <button
              onClick={handleKeycloakLogin}
              className="w-full py-2 px-3 text-[11px] font-medium text-zinc-300 bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 rounded-lg flex items-center justify-center gap-2 transition-colors cursor-pointer"
            >
              <Lock className="w-3 h-3 text-zinc-400" />
              <span>Redirect to Keycloak Authorization</span>
            </button>
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="pt-4 border-t border-zinc-800/80 flex items-center justify-between text-[11px] text-zinc-500">
        <div className="flex items-center gap-1.5">
          <Shield className="w-3.5 h-3.5 text-emerald-400" />
          <span>Encrypted Session BFF</span>
        </div>
        <Link
          href="/"
          className="inline-flex items-center gap-1 text-violet-400 hover:text-violet-300 font-medium transition-colors"
        >
          <ArrowLeft className="w-3 h-3" />
          Back to Catalog
        </Link>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-zinc-950 text-zinc-50">
      <Suspense fallback={<div className="text-xs text-zinc-400">Loading authentication UI...</div>}>
        <LoginContent />
      </Suspense>
    </div>
  );
}
