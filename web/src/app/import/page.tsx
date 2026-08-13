import React from "react";
import { PageContainer } from "@/components/ui/PageContainer";
import { EmptyState } from "@/components/ui/States";

export default function ImportPage() {
  return (
    <PageContainer
      title="Library Import"
      subtitle="Import watch events and ratings from external sources (Letterboxd, Trakt, CSV)"
    >
      <div className="space-y-6">
        <EmptyState
          title="Import Utility Placeholder"
          description="External data ingestion and watch history import workflows will render here upon API integration."
        />
      </div>
    </PageContainer>
  );
}
