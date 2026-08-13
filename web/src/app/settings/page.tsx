import React from "react";
import { PageContainer } from "@/components/ui/PageContainer";
import { EmptyState } from "@/components/ui/States";

export default function SettingsPage() {
  return (
    <PageContainer
      title="Settings"
      subtitle="Application configuration, theme preferences, and sync status"
    >
      <div className="space-y-6">
        <EmptyState
          title="Settings View Placeholder"
          description="Application preferences, account management, and local sync controls will render here."
        />
      </div>
    </PageContainer>
  );
}
