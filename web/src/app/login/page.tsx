"use client";

import React, { Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Clapperboard, Lock, ArrowLeft, Shield, AlertTriangle } from "lucide-react";

function LoginContent() {
  const searchParams = useSearchParams();
  const error = searchParams.get("error");
  const returnTo = searchParams.get("returnTo") || "/dashboard";

  const handleKeycloakLogin = () => {
    window.location.href = `/api/auth/login?returnTo=${encodeURIComponent(returnTo)}`;
  };

  return (
    <div className="w-full max-w-md p-8 rounded-3xl bg-zinc-900/80 border border-zinc-800 shadow-2xl backdrop-blur-xl space-y-6">
      {/* Brand Header */}
      <div className="flex flex-col items-center text-center space-y-2">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-violet-600/30 mb-2">
          <Clapperboard className="w-6 h-6 text-white" />
        </div>
        <h1 className="text-xl font-bold tracking-tight text-zinc-50">
          Sign In to <span className="text-violet-400">CineVault OS</span>
        </h1>
        <p className="text-xs text-zinc-400 max-w-xs leading-relaxed">
          Canonical Identity Provider Authentication (Keycloak OIDC Authorization Code Flow + PKCE S256)
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-3.5 rounded-2xl bg-red-950/40 border border-red-800/60 text-xs text-red-300 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold text-red-200">Authentication Failed</div>
            <div className="text-[11px] text-red-300/80 mt-0.5">{error}</div>
          </div>
        </div>
      )}

      {/* Main OIDC Login Button */}
      <div className="space-y-4">
        <button
          onClick={handleKeycloakLogin}
          className="w-full py-3 px-4 text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 border border-violet-500 rounded-full shadow-lg shadow-violet-600/30 flex items-center justify-center gap-2 transition-all transform active:scale-[0.99] cursor-pointer"
        >
          <Lock className="w-4 h-4" />
          <span>Sign In with Keycloak OIDC</span>
        </button>
      </div>

      {/* Footer Info */}
      <div className="pt-4 border-t border-zinc-800/80 flex items-center justify-between text-[11px] text-zinc-500">
        <div className="flex items-center gap-1.5">
          <Shield className="w-3.5 h-3.5 text-emerald-400" />
          <span>PKCE S256 Enabled</span>
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
