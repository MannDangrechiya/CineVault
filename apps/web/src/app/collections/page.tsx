"use client";

import React from "react";
import Link from "next/link";
import { PageContainer } from "@/components/ui/PageContainer";
import { ArrowRight } from "lucide-react";

interface CollectionItem {
  id: string;
  name: string;
  description: string;
  itemCount: number;
  bannerUrl: string;
  curator: string;
  tags: string[];
}

const mockCollections: CollectionItem[] = [
  {
    id: "dune-saga",
    name: "Dune: The Arrakis Chronicle",
    description: "Denis Villeneuve's complete epic saga tracking Paul Atreides and the Fremen resistance.",
    itemCount: 2,
    bannerUrl: "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1200&q=80",
    curator: "CineVault Curators",
    tags: ["Sci-Fi", "Frank Herbert", "IMAX 70mm"],
  },
  {
    id: "cyberpunk-essentials",
    name: "Cyberpunk & Neo-Noir Canon",
    description: "Atmospheric, rain-slicked cityscapes, rogue replicants, and synthetic consciousness.",
    itemCount: 4,
    bannerUrl: "https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=1200&q=80",
    curator: "AI Neural Curations",
    tags: ["Cyberpunk", "Dystopian", "Synthesizer"],
  },
  {
    id: "nolan-non-linear",
    name: "Christopher Nolan Chronology",
    description: "Time dilation, practical in-camera effects, and 70mm cinematic spectacles.",
    itemCount: 5,
    bannerUrl: "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80",
    curator: "Christopher Nolan Canon",
    tags: ["Time-Bending", "Hans Zimmer", "70mm"],
  },
];

export default function CollectionsPage() {
  return (
    <PageContainer
      title="Collections & Franchises"
      subtitle="Curated title sets, universe marathons, and chronological viewing orders"
    >
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {mockCollections.map((col) => (
            <div
              key={col.id}
              className="group rounded-3xl overflow-hidden bg-zinc-900/40 hover:bg-zinc-900/70 border border-zinc-900 hover:border-zinc-800 transition-all flex flex-col justify-between"
            >
              <div>
                {/* Banner Artwork */}
                <div className="relative h-44 w-full bg-zinc-950 overflow-hidden">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={col.bannerUrl}
                    alt={col.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/40 to-transparent" />
                  <div className="absolute top-3 right-3 px-2.5 py-1 rounded-full text-[10px] font-semibold bg-zinc-950/80 backdrop-blur-md text-zinc-300 border border-zinc-800">
                    {col.itemCount} Titles
                  </div>
                </div>

                {/* Info */}
                <div className="p-5 space-y-2.5">
                  <h3 className="text-sm font-bold text-zinc-100 group-hover:text-violet-400 transition-colors">
                    {col.name}
                  </h3>
                  <p className="text-xs text-zinc-400 leading-relaxed line-clamp-2">
                    {col.description}
                  </p>

                  {/* Tags */}
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
                </div>
              </div>

              {/* Action */}
              <div className="p-5 pt-0">
                <Link
                  href="/movies"
                  className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold text-violet-300 bg-violet-600/10 hover:bg-violet-600/20 border border-violet-500/30 transition-all flex items-center justify-center gap-2"
                >
                  <span>Explore Franchise Set</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </PageContainer>
  );
}
