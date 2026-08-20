"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageContainer } from "@/components/ui/PageContainer";
import {
  Sparkles,
  Bot,
  Users,
  Send,
  Film,
  Plus,
  Check,
  ArrowRight,
  Sliders,
  Compass,
} from "lucide-react";
import {
  queryAssistant,
  getFriendships,
  runGroupMatchmaking,
  AssistantQueryResponse,
  GroupMatchResponse,
  FriendshipItem,
} from "@/lib/api/ai";
import { toggleWatchlistState } from "@/lib/api/personal";

interface ChatMessage {
  id: string;
  sender: "user" | "oracle";
  text: string;
  timestamp: string;
  assistantResponse?: AssistantQueryResponse;
}

const STARTER_PROMPTS = [
  "Recommend a cerebral cyberpunk thriller under 100 minutes",
  "Films similar to Denis Villeneuve's Dune with philosophical depth",
  "What are the highest rated Japanese psychological anime films?",
  "Curate a marathon of non-linear Christopher Nolan cinema",
];

export default function OraclePage() {
  const [activeMode, setActiveMode] = useState<"assistant" | "group">("assistant");

  // ── Mode A: Conversational Assistant State ──────────────────────────────
  const [inputText, setInputText] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome-1",
      sender: "oracle",
      text: "Greetings, Cinephile. I am the CineVault AI Oracle — your grounded conversational cinema intelligence engine. Ask me for personalized recommendations, director deep dives, or marathon viewing plans.",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);

  const queryClient = useQueryClient();

  const assistantMutation = useMutation({
    mutationFn: (query: string) => queryAssistant(query),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          id: `oracle-${Date.now()}`,
          sender: "oracle",
          text: data.response_text,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          assistantResponse: data,
        },
      ]);
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        {
          id: `oracle-err-${Date.now()}`,
          sender: "oracle",
          text: "I encountered an error connecting to the neural reasoning backend. Please try a different query.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    },
  });

  const watchlistMutation = useMutation({
    mutationFn: ({ titleId, inWatchlist }: { titleId: string; inWatchlist: boolean }) =>
      toggleWatchlistState(titleId, inWatchlist),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlist"] });
    },
  });

  const [addedWatchlistIds, setAddedWatchlistIds] = useState<Record<string, boolean>>({});

  const handleSendMessage = (textToSend?: string) => {
    const text = (textToSend || inputText).trim();
    if (!text || assistantMutation.isPending) return;

    setMessages((prev) => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        sender: "user",
        text,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      },
    ]);
    setInputText("");
    assistantMutation.mutate(text);
  };

  const handleToggleWatchlist = (titleId: string) => {
    const nextState = !addedWatchlistIds[titleId];
    setAddedWatchlistIds((prev) => ({ ...prev, [titleId]: nextState }));
    watchlistMutation.mutate({ titleId, inWatchlist: nextState });
  };

  // ── Mode B: Group Consensus Matchmaker State ────────────────────────────
  const { data: friendships = [] } = useQuery({
    queryKey: ["friendships"],
    queryFn: getFriendships,
  });

  const [selectedFriendIds, setSelectedFriendIds] = useState<string[]>([]);
  const [groupMood, setGroupMood] = useState("");
  const [groupResult, setGroupResult] = useState<GroupMatchResponse | null>(null);

  const groupMutation = useMutation({
    mutationFn: () => runGroupMatchmaking(selectedFriendIds, groupMood || "Cerebral Sci-Fi Marathon"),
    onSuccess: (data) => {
      setGroupResult(data);
    },
  });

  const toggleSelectFriend = (friendId: string) => {
    setSelectedFriendIds((prev) =>
      prev.includes(friendId) ? prev.filter((id) => id !== friendId) : [...prev, friendId]
    );
  };

  return (
    <PageContainer
      title="AI Oracle & Consensus Matchmaker"
      subtitle="Conversational neural intelligence, grounded catalog discovery, and multi-user taste vector consensus"
    >
      <div className="space-y-6">
        {/* Mode Selector Tabs */}
        <div className="flex items-center justify-between gap-4 pb-2 border-b border-zinc-900">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveMode("assistant")}
              className={`flex items-center gap-2 px-4 py-2 rounded-2xl text-xs font-semibold transition-all cursor-pointer ${
                activeMode === "assistant"
                  ? "bg-violet-600 text-white shadow-lg shadow-violet-600/30"
                  : "text-zinc-400 hover:text-zinc-200 bg-zinc-900/60 hover:bg-zinc-900 border border-zinc-800"
              }`}
            >
              <Bot className="w-4 h-4" />
              <span>Conversational Oracle</span>
            </button>

            <button
              onClick={() => setActiveMode("group")}
              className={`flex items-center gap-2 px-4 py-2 rounded-2xl text-xs font-semibold transition-all cursor-pointer ${
                activeMode === "group"
                  ? "bg-violet-600 text-white shadow-lg shadow-violet-600/30"
                  : "text-zinc-400 hover:text-zinc-200 bg-zinc-900/60 hover:bg-zinc-900 border border-zinc-800"
              }`}
            >
              <Users className="w-4 h-4" />
              <span>Group Taste Matchmaker</span>
            </button>
          </div>

          <div className="hidden sm:flex items-center gap-2 text-xs text-zinc-400">
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            <span>384-Dim Neural Vector Engine</span>
          </div>
        </div>

        {/* ── MODE A: CONVERSATIONAL ASSISTANT ────────────────────────────── */}
        {activeMode === "assistant" && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Left 3 Columns: Chat Thread & Input */}
            <div className="lg:col-span-3 flex flex-col h-[700px] rounded-3xl bg-zinc-900/40 border border-zinc-900 overflow-hidden">
              {/* Messages Container */}
              <div className="flex-1 p-6 overflow-y-auto space-y-6">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex gap-3 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
                  >
                    {msg.sender === "oracle" && (
                      <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center text-white shrink-0 shadow-md">
                        <Sparkles className="w-4 h-4" />
                      </div>
                    )}

                    <div
                      className={`max-w-2xl rounded-2xl p-4 space-y-3 ${
                        msg.sender === "user"
                          ? "bg-violet-600 text-white"
                          : "bg-zinc-950/80 border border-zinc-850 text-zinc-200"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-4">
                        <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
                          {msg.sender === "user" ? "You" : "CineVault Oracle"}
                        </span>
                        <span className="text-[10px] text-zinc-500">{msg.timestamp}</span>
                      </div>

                      <p className="text-xs sm:text-sm leading-relaxed whitespace-pre-wrap">
                        {msg.text}
                      </p>

                      {/* Structured Intent Badges */}
                      {msg.assistantResponse?.intent && (
                        <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-zinc-900">
                          <span className="px-2 py-0.5 rounded-md text-[10px] bg-violet-950/80 text-violet-300 border border-violet-800/40">
                            Intent: {msg.assistantResponse.intent.detected_intent_mode}
                          </span>
                          {msg.assistantResponse.intent.target_genres.map((g) => (
                            <span
                              key={g}
                              className="px-2 py-0.5 rounded-md text-[10px] bg-zinc-900 text-zinc-300 border border-zinc-800"
                            >
                              {g}
                            </span>
                          ))}
                          {msg.assistantResponse.intent.target_directors.map((d) => (
                            <span
                              key={d}
                              className="px-2 py-0.5 rounded-md text-[10px] bg-amber-950/50 text-amber-300 border border-amber-800/40"
                            >
                              Dir: {d}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Matched Title Cards */}
                      {msg.assistantResponse?.matched_titles &&
                        msg.assistantResponse.matched_titles.length > 0 && (
                          <div className="space-y-2 pt-3">
                            <p className="text-[11px] font-bold text-zinc-300 flex items-center gap-1.5">
                              <Film className="w-3.5 h-3.5 text-violet-400" />
                              <span>Recommended Titles</span>
                            </p>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                              {msg.assistantResponse.matched_titles.map((title, idx) => {
                                const titleId = title.id || title.title_id || `rec-${idx}`;
                                const isAdded = addedWatchlistIds[titleId];
                                const poster =
                                  title.poster_url ||
                                  "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=400&q=80";

                                return (
                                  <div
                                    key={titleId}
                                    className="p-2.5 rounded-xl bg-zinc-900/90 border border-zinc-800 flex gap-3 group hover:border-violet-500/40 transition-all"
                                  >
                                    <div className="w-12 h-16 rounded-lg bg-zinc-950 overflow-hidden shrink-0">
                                      {/* eslint-disable-next-line @next/next/no-img-element */}
                                      <img
                                        src={poster}
                                        alt={title.canonical_title}
                                        className="w-full h-full object-cover"
                                      />
                                    </div>

                                    <div className="flex-1 min-w-0 flex flex-col justify-between">
                                      <div>
                                        <h4 className="text-xs font-bold text-zinc-100 truncate">
                                          {title.canonical_title}
                                        </h4>
                                        <p className="text-[10px] text-zinc-400">
                                          {title.production_year} • {title.genres?.slice(0, 2).join(", ") || "Cinema"}
                                        </p>
                                      </div>

                                      <div className="flex items-center gap-2 pt-1">
                                        <button
                                          onClick={() => handleToggleWatchlist(titleId)}
                                          className={`px-2 py-1 rounded-md text-[10px] font-semibold flex items-center gap-1 transition-all cursor-pointer ${
                                            isAdded
                                              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                                              : "bg-violet-600/20 hover:bg-violet-600/30 text-violet-300 border border-violet-500/30"
                                          }`}
                                        >
                                          {isAdded ? <Check className="w-2.5 h-2.5" /> : <Plus className="w-2.5 h-2.5" />}
                                          <span>{isAdded ? "In Watchlist" : "Watchlist"}</span>
                                        </button>

                                        <Link
                                          href={`/movies/${titleId}`}
                                          className="text-[10px] text-zinc-400 hover:text-violet-300 flex items-center gap-0.5"
                                        >
                                          <span>Details</span>
                                          <ArrowRight className="w-2.5 h-2.5" />
                                        </Link>
                                      </div>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}
                    </div>
                  </div>
                ))}

                {assistantMutation.isPending && (
                  <div className="flex gap-3 justify-start items-center">
                    <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center text-white shrink-0 animate-pulse">
                      <Sparkles className="w-4 h-4 animate-spin" />
                    </div>
                    <div className="rounded-2xl p-4 bg-zinc-950/80 border border-zinc-850 text-zinc-400 text-xs flex items-center gap-2">
                      <span>Reasoning across 88,000+ canonical titles...</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Chat Input Bar */}
              <div className="p-4 bg-zinc-950/80 border-t border-zinc-900 space-y-3">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendMessage();
                  }}
                  className="flex items-center gap-3"
                >
                  <input
                    type="text"
                    placeholder="Ask Oracle: 'Find 90s psychological anime thrillers under 100 mins'..."
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    disabled={assistantMutation.isPending}
                    className="flex-1 px-4 py-3 rounded-2xl bg-zinc-900 border border-zinc-800 text-xs sm:text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500 transition-colors"
                  />
                  <button
                    type="submit"
                    disabled={assistantMutation.isPending || !inputText.trim()}
                    className="p-3 rounded-2xl bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white shadow-lg shadow-violet-600/30 transition-all cursor-pointer shrink-0"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </form>
              </div>
            </div>

            {/* Right Column: Starter Prompts & Capabilities */}
            <div className="space-y-4">
              <div className="p-5 rounded-3xl bg-zinc-900/40 border border-zinc-900 space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold text-zinc-200">
                  <Compass className="w-4 h-4 text-violet-400" />
                  <span>Curated Discovery Prompts</span>
                </div>

                <div className="space-y-2">
                  {STARTER_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      onClick={() => handleSendMessage(prompt)}
                      disabled={assistantMutation.isPending}
                      className="w-full text-left p-3 rounded-2xl bg-zinc-950/60 hover:bg-zinc-950 border border-zinc-850 hover:border-violet-500/40 text-xs text-zinc-300 hover:text-white transition-all cursor-pointer"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>

              <div className="p-5 rounded-3xl bg-zinc-900/40 border border-zinc-900 space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold text-zinc-200">
                  <Sliders className="w-4 h-4 text-emerald-400" />
                  <span>Oracle Core Capabilities</span>
                </div>
                <ul className="text-[11px] text-zinc-400 space-y-2 leading-relaxed">
                  <li className="flex items-start gap-2">
                    <span className="text-violet-400">•</span>
                    <span><strong>Grounded Reasoning:</strong> 100% zero-hallucination factual catalog validation.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-violet-400">•</span>
                    <span><strong>Vector Semantic Search:</strong> High-dimensional aesthetic and thematic matching.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-violet-400">•</span>
                    <span><strong>Franchise Marathons:</strong> Automated chronological viewing orders.</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* ── MODE B: GROUP TASTE MATCHMAKER ──────────────────────────────── */}
        {activeMode === "group" && (
          <div className="space-y-6">
            {/* Setup Form */}
            <div className="p-6 rounded-3xl bg-zinc-900/40 border border-zinc-900 space-y-6">
              <div className="space-y-1">
                <h3 className="text-base font-bold text-zinc-100 flex items-center gap-2">
                  <Users className="w-5 h-5 text-violet-400" />
                  <span>Group Taste Consensus Engine</span>
                </h3>
                <p className="text-xs text-zinc-400">
                  Select friends from your network to calculate the mathematical mean taste vector and generate consensus movie night recommendations.
                </p>
              </div>

              {/* Friend Selector Grid */}
              <div className="space-y-3">
                <label className="text-xs font-semibold text-zinc-300 flex items-center justify-between">
                  <span>Select Friends to Include ({selectedFriendIds.length} selected)</span>
                  <span className="text-[11px] text-zinc-500">Accepted friendships required</span>
                </label>

                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                  {friendships.map((f: FriendshipItem) => {
                    const isSelected = selectedFriendIds.includes(f.friend_id);
                    const avatar =
                      f.avatar_url ||
                      "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80";

                    return (
                      <button
                        key={f.friend_id}
                        type="button"
                        onClick={() => toggleSelectFriend(f.friend_id)}
                        className={`p-3.5 rounded-2xl border text-left flex items-center justify-between gap-3 transition-all cursor-pointer ${
                          isSelected
                            ? "bg-violet-600/15 border-violet-500 shadow-md shadow-violet-950/30"
                            : "bg-zinc-950/60 border-zinc-800 hover:border-zinc-700"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src={avatar}
                            alt={f.friend_name}
                            className="w-10 h-10 rounded-full object-cover border border-zinc-700"
                          />
                          <div>
                            <p className="text-xs font-bold text-zinc-100">{f.friend_name}</p>
                            <p className="text-[10px] text-zinc-400">@{f.friend_username}</p>
                          </div>
                        </div>

                        <div
                          className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] border ${
                            isSelected
                              ? "bg-violet-600 border-violet-500 text-white"
                              : "border-zinc-700 text-transparent"
                          }`}
                        >
                          ✓
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Mood Input & Dispatch Button */}
              <div className="flex flex-col sm:flex-row gap-4 pt-2">
                <input
                  type="text"
                  placeholder="Set Watch Mood: e.g. 'Mind-bending cyberpunk thriller for Friday night'..."
                  value={groupMood}
                  onChange={(e) => setGroupMood(e.target.value)}
                  className="flex-1 px-4 py-3 rounded-2xl bg-zinc-950 border border-zinc-800 text-xs sm:text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500 transition-colors"
                />

                <button
                  type="button"
                  onClick={() => groupMutation.mutate()}
                  disabled={selectedFriendIds.length === 0 || groupMutation.isPending}
                  className="px-6 py-3 rounded-2xl text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 disabled:opacity-50 transition-all cursor-pointer shadow-lg shadow-violet-600/30 shrink-0 flex items-center justify-center gap-2"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>{groupMutation.isPending ? "Synthesizing Vectors..." : "Generate Group Consensus"}</span>
                </button>
              </div>
            </div>

            {/* Results Presentation */}
            {groupResult && (
              <div className="p-6 rounded-3xl bg-zinc-900/40 border border-zinc-900 space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-900">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">
                      Consensus Calculated
                    </span>
                    <h3 className="text-lg font-bold text-zinc-100 mt-0.5">
                      Mood: &ldquo;{groupResult.mood}&rdquo;
                    </h3>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-violet-600/20 text-violet-300 border border-violet-500/30">
                      {groupResult.group_size} Group Members
                    </span>
                  </div>
                </div>

                {/* AI Rationale commentary */}
                <div className="p-4 rounded-2xl bg-zinc-950/80 border border-zinc-850 space-y-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-zinc-200">
                    <Sparkles className="w-4 h-4 text-emerald-400" />
                    <span>AI Synthesis & Mathematical Rationale</span>
                  </div>
                  <p className="text-xs sm:text-sm text-zinc-300 leading-relaxed">
                    {groupResult.ai_recommendation}
                  </p>
                </div>

                {/* Recommended Titles Grid */}
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-zinc-200 uppercase tracking-wider">
                    Recommended Consensus Titles
                  </h4>

                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                    {groupResult.recommended_titles.map((titleName, i) => (
                      <div
                        key={titleName}
                        className="p-4 rounded-2xl bg-zinc-950/90 border border-zinc-800 space-y-3 flex flex-col justify-between hover:border-violet-500/40 transition-all group"
                      >
                        <div className="space-y-1.5">
                          <div className="w-8 h-8 rounded-xl bg-violet-600/20 text-violet-400 flex items-center justify-center text-xs font-bold border border-violet-500/30">
                            #{i + 1}
                          </div>
                          <h5 className="text-xs font-bold text-zinc-100 group-hover:text-violet-400 transition-colors">
                            {titleName}
                          </h5>
                          <p className="text-[11px] text-zinc-400">
                            High mutual resonance across all selected taste profiles.
                          </p>
                        </div>

                        <Link
                          href="/movies"
                          className="w-full py-2 rounded-xl text-[11px] font-semibold text-violet-300 bg-violet-600/10 hover:bg-violet-600/20 border border-violet-500/30 transition-all flex items-center justify-center gap-1.5"
                        >
                          <span>Explore in Catalog</span>
                          <ArrowRight className="w-3 h-3" />
                        </Link>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </PageContainer>
  );
}
