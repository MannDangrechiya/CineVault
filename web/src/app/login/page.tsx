import React from "react";
import Link from "next/link";
import { Clapperboard, Lock, ArrowLeft, Shield } from "lucide-react";

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-950 text-slate-100">
      <div className="w-full max-w-md p-8 rounded-2xl bg-slate-900/60 border border-slate-800/80 shadow-2xl backdrop-blur-xl space-y-6">
        {/* Brand Header */}
        <div className="flex flex-col items-center text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-violet-900/40 mb-2">
            <Clapperboard className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100">
            Sign In to <span className="text-violet-400">CineVault</span>
          </h1>
          <p className="text-xs text-slate-400 max-w-xs">
            Web Client Authentication Placeholder (Authentication logic not implemented in Day 1 foundation)
          </p>
        </div>

        {/* Form Placeholder */}
        <div className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-300">Email Address</label>
            <input
              type="email"
              disabled
              placeholder="user@cinevault.local (Placeholder)"
              className="w-full px-3.5 py-2 text-xs bg-slate-950/80 border border-slate-800 rounded-lg text-slate-400 placeholder:text-slate-600 focus:outline-none cursor-not-allowed"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-300">Password</label>
            <input
              type="password"
              disabled
              placeholder="•••••••••••• (Placeholder)"
              className="w-full px-3.5 py-2 text-xs bg-slate-950/80 border border-slate-800 rounded-lg text-slate-400 placeholder:text-slate-600 focus:outline-none cursor-not-allowed"
            />
          </div>

          <button
            disabled
            className="w-full py-2.5 px-4 text-xs font-semibold text-slate-400 bg-violet-950/40 border border-violet-900/50 rounded-xl flex items-center justify-center gap-2 cursor-not-allowed opacity-70"
          >
            <Lock className="w-3.5 h-3.5" />
            Sign In (Placeholder Only)
          </button>
        </div>

        {/* Environment Info */}
        <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
          <div className="flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-slate-400" />
            <span>OIDC / PKCE Ready</span>
          </div>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1 text-violet-400 hover:text-violet-300 font-medium transition-colors"
          >
            <ArrowLeft className="w-3 h-3" />
            Back to App
          </Link>
        </div>
      </div>
    </div>
  );
}
