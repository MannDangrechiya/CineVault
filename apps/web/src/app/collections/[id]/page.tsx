"use client";

import React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageContainer } from "@/components/ui/PageContainer";
import { LoadingState, ErrorState } from "@/components/ui/States";
import { ArrowLeft, Film, Tv, Trash2, Lock, Globe, Layers } from "lucide-react";
import { getCollectionDetail, removeCollectionItem } from "@/lib/api/collections";

export default function CollectionDetailPage() {
  const params = useParams();
  const id = typeof params.id === "string" ? params.id : "";
  const queryClient = useQueryClient();

  // Standalone collection view -- previously a collection could be created
  // and deleted but never actually populated or browsed: GET /v1/personal/
  // collections/{id} + the item add/remove endpoints didn't exist at all
  // (see WEB_FEATURE_AUDIT.md). This mirrors the Watch Club/Pick Room
  // standalone-page pattern used elsewhere.
  const {
    data: detail,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["collection-detail", id],
    queryFn: () => getCollectionDetail(id),
    enabled: Boolean(id),
  });

  const removeMutation = useMutation({
    mutationFn: (titleId: string) => removeCollectionItem(id, titleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collection-detail", id] });
      queryClient.invalidateQueries({ queryKey: ["collections"] });
    },
  });

  if (isLoading) {
    return (
      <PageContainer title="Collection" subtitle="Loading your curated titles...">
        <div className="p-8">
          <LoadingState message="Loading collection..." />
        </div>
      </PageContainer>
    );
  }

  if (isError || !detail) {
    return (
      <PageContainer title="Collection Not Found" subtitle="This collection does not exist.">
        <ErrorState
          title="Collection Not Found"
          description="It may have been deleted, or you may not have access to it."
          onAction={() => refetch()}
        />
        <div className="text-center mt-4">
          <Link href="/collections" className="text-xs text-violet-400 hover:underline">
            ← Back to Collections
          </Link>
        </div>
      </PageContainer>
    );
  }

  const { collection, items } = detail;

  return (
    <PageContainer
      title={collection.name}
      subtitle={collection.description || `${items.length} curated ${items.length === 1 ? "title" : "titles"}`}
      action={
        <Link
          href="/collections"
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200 transition-all"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>All Collections</span>
        </Link>
      }
    >
      <div className="space-y-6">
        <div className="flex items-center gap-3 text-xs text-zinc-400">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-zinc-900/60 border border-zinc-800">
            {collection.is_private ? (
              <Lock className="w-3 h-3 text-amber-400" />
            ) : (
              <Globe className="w-3 h-3 text-violet-400" />
            )}
            <span>{collection.is_private ? "Private" : "Public"}</span>
          </span>
          <span>Curated by {collection.curator}</span>
        </div>

        {items.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-center rounded-2xl bg-zinc-900/30 border border-zinc-900 backdrop-blur-md min-h-[240px]">
            <div className="w-12 h-12 rounded-2xl bg-zinc-900 flex items-center justify-center mb-4 border border-zinc-800">
              <Layers className="w-6 h-6 text-zinc-500" />
            </div>
            <h3 className="text-base font-bold text-zinc-100 mb-1">No Titles Yet</h3>
            <p className="text-xs sm:text-sm text-zinc-400 max-w-md mb-6 leading-relaxed">
              Add titles to this collection from any movie or series page using &ldquo;Add to Collection.&rdquo;
            </p>
            <Link
              href="/movies"
              className="inline-flex items-center gap-2 px-5 py-2 text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 rounded-full shadow-lg shadow-violet-600/20 transition-all"
            >
              <Film className="w-3.5 h-3.5" />
              <span>Browse Movies Catalog</span>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {items.map((item) => {
              const isRemoving = removeMutation.isPending && removeMutation.variables === item.title_id;
              return (
                <div
                  key={item.item_id}
                  className={`group relative flex flex-col rounded-2xl overflow-hidden bg-zinc-900/40 hover:bg-zinc-900/70 border border-zinc-900 hover:border-zinc-800 transition-all p-3 ${
                    isRemoving ? "opacity-40 pointer-events-none" : ""
                  }`}
                >
                  <Link href={`/movies/${item.title_id}`} className="block">
                    <div className="relative aspect-[2/3] w-full bg-zinc-950 rounded-xl overflow-hidden mb-2.5">
                      {item.poster_url ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={item.poster_url}
                          alt={item.canonical_title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-gradient-to-b from-zinc-900 to-zinc-950 text-zinc-700">
                          {item.content_type === "MOVIE" ? <Film className="w-8 h-8" /> : <Tv className="w-8 h-8" />}
                        </div>
                      )}
                    </div>
                    <h4 className="text-xs font-bold text-zinc-100 group-hover:text-violet-400 transition-colors line-clamp-1">
                      {item.canonical_title}
                    </h4>
                    <div className="flex items-center justify-between text-[11px] text-zinc-500 mt-1">
                      <span>{item.production_year ?? "—"}</span>
                    </div>
                  </Link>
                  {item.notes && (
                    <p className="text-[10px] text-zinc-500 italic mt-1.5 line-clamp-2">{item.notes}</p>
                  )}
                  <div className="flex items-center justify-end pt-2.5 mt-2.5 border-t border-zinc-900/80">
                    <button
                      onClick={() => removeMutation.mutate(item.title_id)}
                      disabled={removeMutation.isPending}
                      title="Remove from Collection"
                      className="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-zinc-800/80 transition-colors cursor-pointer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </PageContainer>
  );
}
