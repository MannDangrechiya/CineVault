"use client";

import React from "react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { MobileNav } from "./MobileNav";
import { usePathname } from "next/navigation";

export const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const pathname = usePathname();
  const isLoginPage = pathname === "/login";

  if (isLoginPage) {
    return <main className="min-h-screen bg-zinc-950 text-zinc-50">{children}</main>;
  }

  return (
    <div className="min-h-screen flex bg-zinc-950 text-zinc-50 selection:bg-violet-600/30 selection:text-violet-200">
      {/* Responsive Desktop Frosted Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 pb-16 md:pb-0">
        {/* Sticky Frosted Glass Header */}
        <Header />

        {/* Page Main Content Container */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto flex flex-col">
          <div className="flex-1">
            {children}
          </div>
          
          {/* Credits Footer */}
          <footer className="w-full text-center py-8 mt-12 border-t border-white/5 text-sm text-zinc-500">
            <p>
              Designed and built by <span className="text-zinc-300 font-medium">Mann Dangrechiya</span>
            </p>
          </footer>
        </main>
      </div>

      {/* Mobile Bottom Bar Navigation */}
      <MobileNav />
    </div>
  );
};
