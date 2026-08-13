import React from "react";
import { PageContainer } from "@/components/ui/PageContainer";
import { EmptyState } from "@/components/ui/States";

export default function SeriesPage() {
  return (
    <PageContainer
      title="TV Series Catalog"
      subtitle="Episodic title hierarchy, seasons, and episode tracking"
    >
      <div className="space-y-6">
        <EmptyState
          title="TV Series Catalog Placeholder"
          description="Episodic series hierarchy browser will render here upon API integration."
        />
      </div>
    </PageContainer>
  );
}
