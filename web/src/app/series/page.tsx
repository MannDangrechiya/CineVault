"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { PageContainer } from "@/components/ui/PageContainer";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/States";
import { TitleCard } from "@/components/catalog/TitleCard";
import { getTitles } from "@/lib/api/titles";

export default function SeriesPage() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["titles", "TV_SERIES"],
    queryFn: () => getTitles({ content_type: "TV_SERIES", limit: 50 }),
  });

  return (
    <PageContainer
      title="TV Series Catalog"
      subtitle="Episodic title hierarchy, seasons, and episode tracking"
    >
      <div className="space-y-6">
        {isLoading && <LoadingState message="Loading TV series catalog..." />}

        {isError && (
          <ErrorState
            title="Unable to Load TV Series Catalog"
            description={
              error instanceof Error
                ? error.message
                : "Failed to connect to local CineVault FastAPI backend service."
            }
            onAction={() => refetch()}
          />
        )}

        {!isLoading && !isError && data?.data && data.data.length === 0 && (
          <EmptyState
            title="No TV Series in Catalog"
            description="There are currently no TV series records returned by the canonical API."
          />
        )}

        {!isLoading && !isError && data?.data && data.data.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {data.data.map((series, idx) => (
              <TitleCard
                key={series.id}
                title={series}
                matchScore={92 - (idx % 7) * 4}
              />
            ))}
          </div>
        )}
      </div>
    </PageContainer>
  );
}
