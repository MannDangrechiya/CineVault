"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageContainer } from "@/components/ui/PageContainer";
import {
  Plus,
  ArrowRight,
  Trash2,
  FolderPlus,
  X,
  Lock,
  Globe,
} from "lucide-react";
import {
  getCollections,
  createCollection,
  deleteCollection,
} from "@/lib/api/collections";
import { EmptyState, ErrorState } from "@/components/ui/States";

function CollectionsSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
      {[1, 2, 3].map((n) => (
        <div
          key={n}
          className="rounded-3xl overflow-hidden bg-zinc-900/30 border border-zinc-900 flex flex-col justify-between"
        >
          <div className="h-44 w-full bg-zinc-800/60" />
          <div className="p-5 space-y-3">
            <div className="w-3/4 h-5 bg-zinc-800/60 rounded" />
            <div className="w-full h-3 bg-zinc-800/40 rounded" />
            <div className="w-2/3 h-3 bg-zinc-800/40 rounded" />
            <div className="flex gap-2 pt-2">
              <div className="w-16 h-4 bg-zinc-800/40 rounded-lg" />
              <div className="w-20 h-4 bg-zinc-800/40 rounded-lg" />
            </div>
          </div>
          <div className="p-5 pt-0">
            <div className="w-full h-9 bg-zinc-800/50 rounded-xl" />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function CollectionsPage() {
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [tagsInput, setTagsInput] = useState("");
  const [bannerUrl, setBannerUrl] = useState("");
  const [isPrivate, setIsPrivate] = useState(true);

  const queryClient = useQueryClient();

  const {
    data: allCollections = [],
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["collections"],
    queryFn: getCollections,
  });

  // Clean, uncluttered preview grid: show the 10 most recent collections.
  const collections = allCollections.slice(0, 10);

  const createMutation = useMutation({
    mutationFn: createCollection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collections"] });
      setIsCreateOpen(false);
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteCollection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collections"] });
    },
  });

  const resetForm = () => {
    setName("");
    setDescription("");
    setTagsInput("");
    setBannerUrl("");
    setIsPrivate(true);
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const tags = tagsInput
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

    createMutation.mutate({
      name: name.trim(),
      description: description.trim() || undefined,
      tags: tags.length > 0 ? tags : ["Curated"],
      banner_url:
        bannerUrl.trim() ||
        "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1200&q=80",
      is_private: isPrivate,
    });
  };

  return (
    <PageContainer
      title="Collections & Franchises"
      subtitle="Curated title sets, universe marathons, and chronological viewing orders"
      action={
        <button
          onClick={() => setIsCreateOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 rounded-full shadow-lg shadow-violet-600/30 transition-all cursor-pointer"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Create Collection</span>
        </button>
      }
    >
      <div className="space-y-6">
        {/* Collections Grid */}
        {isLoading ? (
          <CollectionsSkeleton />
        ) : isError ? (
          <ErrorState
            title="Failed to Load Collections"
            description="Unable to reach the CineVault collections service. Please try again."
            onAction={() => refetch()}
          />
        ) : collections.length === 0 ? (
          <EmptyState
            title="No Collections Found"
            description="Create your first curated franchise set or personal custom list."
            actionLabel="Create Collection"
            onAction={() => setIsCreateOpen(true)}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {collections.map((col) => {
              const banner =
                col.banner_url ||
                "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1200&q=80";
              const isDeleting =
                deleteMutation.isPending && deleteMutation.variables === col.id;

              return (
                <div
                  key={col.id}
                  className={`group rounded-3xl overflow-hidden bg-zinc-900/40 hover:bg-zinc-900/70 border border-zinc-900 hover:border-zinc-800 transition-all flex flex-col justify-between ${
                    isDeleting ? "opacity-40 pointer-events-none" : ""
                  }`}
                >
                  <div>
                    {/* Banner Artwork */}
                    <div className="relative h-44 w-full bg-zinc-950 overflow-hidden">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={banner}
                        alt={col.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/40 to-transparent" />

                      {/* Header Badges */}
                      <div className="absolute top-3 left-3 right-3 flex items-center justify-between">
                        <span className="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-zinc-950/80 backdrop-blur-md text-zinc-300 border border-zinc-800 flex items-center gap-1">
                          {col.is_private ? (
                            <Lock className="w-2.5 h-2.5 text-amber-400" />
                          ) : (
                            <Globe className="w-2.5 h-2.5 text-violet-400" />
                          )}
                          <span>{col.curator}</span>
                        </span>

                        <div className="flex items-center gap-2">
                          <span className="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-zinc-950/80 backdrop-blur-md text-zinc-300 border border-zinc-800">
                            {col.item_count} Titles
                          </span>
                          {col.is_custom && (
                            <button
                              onClick={() => deleteMutation.mutate(col.id)}
                              title="Delete Collection"
                              className="p-1 rounded-full bg-zinc-950/80 backdrop-blur-md text-zinc-400 hover:text-red-400 border border-zinc-800 hover:border-red-500/40 transition-colors cursor-pointer"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Info */}
                    <div className="p-5 space-y-2.5">
                      <h3 className="text-sm font-bold text-zinc-100 group-hover:text-violet-400 transition-colors line-clamp-1">
                        {col.name}
                      </h3>
                      {col.description && (
                        <p className="text-xs text-zinc-400 leading-relaxed line-clamp-2">
                          {col.description}
                        </p>
                      )}

                      {/* Tags */}
                      {col.tags && col.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 pt-1">
                          {col.tags.map((tag) => (
                            <span
                              key={tag}
                              className="px-2 py-0.5 text-[10px] rounded-lg bg-zinc-950/80 border border-zinc-850 text-zinc-400"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Action */}
                  <div className="p-5 pt-0">
                    <Link
                      href={`/collections/${col.id}`}
                      className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold text-violet-300 bg-violet-600/10 hover:bg-violet-600/20 border border-violet-500/30 transition-all flex items-center justify-center gap-2"
                    >
                      <span>Explore Collection</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Create Collection Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="relative w-full max-w-md p-6 rounded-3xl bg-zinc-900 border border-zinc-800 shadow-2xl shadow-violet-950/20 space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-violet-600/15 border border-violet-500/30 text-violet-400">
                  <FolderPlus className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-zinc-100">
                    Create New Collection
                  </h3>
                  <p className="text-[11px] text-zinc-400">
                    Curate and organize your personal film canons
                  </p>
                </div>
              </div>

              <button
                onClick={() => setIsCreateOpen(false)}
                className="p-1.5 rounded-xl text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-300">
                  Collection Name <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Neo-Tokyo Cyberpunk Canon"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-zinc-950 border border-zinc-800 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500 transition-colors"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-300">
                  Description
                </label>
                <textarea
                  rows={2}
                  placeholder="Brief synopsis or curation theme..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-zinc-950 border border-zinc-800 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500 transition-colors resize-none"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-300">
                  Tags (comma separated)
                </label>
                <input
                  type="text"
                  placeholder="Sci-Fi, 70mm, Dystopian"
                  value={tagsInput}
                  onChange={(e) => setTagsInput(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-zinc-950 border border-zinc-800 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500 transition-colors"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-300">
                  Banner Backdrop URL (optional)
                </label>
                <input
                  type="url"
                  placeholder="https://images.unsplash.com/..."
                  value={bannerUrl}
                  onChange={(e) => setBannerUrl(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-zinc-950 border border-zinc-800 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500 transition-colors"
                />
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-zinc-950 border border-zinc-800">
                <div className="flex items-center gap-2">
                  <Lock className="w-3.5 h-3.5 text-zinc-400" />
                  <div>
                    <p className="text-xs font-medium text-zinc-200">
                      Private Collection
                    </p>
                    <p className="text-[10px] text-zinc-500">
                      Only visible to your account (CAT-2)
                    </p>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={isPrivate}
                  onChange={(e) => setIsPrivate(e.target.checked)}
                  className="w-4 h-4 rounded accent-violet-600 bg-zinc-900 border-zinc-700"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-medium text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending || !name.trim()}
                  className="px-5 py-2 rounded-xl text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 disabled:opacity-50 transition-all cursor-pointer shadow-lg shadow-violet-600/30"
                >
                  {createMutation.isPending ? "Creating..." : "Create Collection"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </PageContainer>
  );
}
