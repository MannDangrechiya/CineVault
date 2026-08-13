import React from "react";
import { PageContainer } from "@/components/ui/PageContainer";
import { EmptyState } from "@/components/ui/States";

export default function MoviesPage() {
  return (
    <PageContainer
      title="Movies Catalog"
      subtitle="Canonical feature films, editions, releases, and festival submissions"
    >
      <div className="space-y-6">
        <EmptyState
          title="Movies Catalog Placeholder"
          description="Canonical feature film catalog browser will render here upon API integration."
        />
      </div>
    </PageContainer>
  );
}
