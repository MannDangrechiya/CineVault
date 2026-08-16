import React from "react";
import { PageContainer } from "@/components/ui/PageContainer";
import { EmptyState } from "@/components/ui/States";

export default function ImportPage() {
  return (
    <PageContainer
      title="Library Data Portability & Import"
      subtitle="Import watch events, ratings, and lists from Letterboxd, Trakt, and CSV"
    >
      <div className="space-y-6">
        <EmptyState
          title="Data Portability Pipeline"
          description="Sovereign CSV/JSON ingestion pipeline and conflict-safe sync engine."
        />
      </div>
    </PageContainer>
  );
}
