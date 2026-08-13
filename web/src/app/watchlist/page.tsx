import React from "react";
import { PageContainer } from "@/components/ui/PageContainer";
import { EmptyState } from "@/components/ui/States";

export default function WatchlistPage() {
  return (
    <PageContainer
      title="Watchlist"
      subtitle="Saved titles queued for future viewing"
    >
      <div className="space-y-6">
        <EmptyState
          title="Watchlist Placeholder"
          description="User title watchlist items will render here upon API integration."
        />
      </div>
    </PageContainer>
  );
}
