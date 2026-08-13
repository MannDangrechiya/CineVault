import React from "react";
import { PageContainer } from "@/components/ui/PageContainer";
import { EmptyState } from "@/components/ui/States";

export default function HistoryPage() {
  return (
    <PageContainer
      title="Watch History"
      subtitle="Append-only historical viewing events log (ADR-003 / CAT-2)"
    >
      <div className="space-y-6">
        <EmptyState
          title="Watch History Log Placeholder"
          description="Append-only watch events (CAT-2) will be listed here upon API integration."
        />
      </div>
    </PageContainer>
  );
}
