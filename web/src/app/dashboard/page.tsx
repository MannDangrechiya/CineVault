import React from "react";
import { PageContainer } from "@/components/ui/PageContainer";
import { EmptyState } from "@/components/ui/States";

export default function DashboardPage() {
  return (
    <PageContainer
      title="Dashboard"
      subtitle="Overview of user watch activity, catalog stats, and personal recommendations"
    >
      <div className="space-y-6">
        <EmptyState
          title="Dashboard View Placeholder"
          description="Backend data binding is intentionally omitted in Day 1 foundation to prevent architectural debt. API integration will connect here in subsequent steps."
        />
      </div>
    </PageContainer>
  );
}
