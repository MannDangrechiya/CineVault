import React from "react";
import { PageContainer } from "@/components/ui/PageContainer";
import { EmptyState } from "@/components/ui/States";

export default function CollectionsPage() {
  return (
    <PageContainer
      title="Collections & Franchises"
      subtitle="Curated title sets, universes, and chronological viewing orders"
    >
      <div className="space-y-6">
        <EmptyState
          title="Collections Placeholder"
          description="Curated collections and franchise viewing orders will render here upon API integration."
        />
      </div>
    </PageContainer>
  );
}
