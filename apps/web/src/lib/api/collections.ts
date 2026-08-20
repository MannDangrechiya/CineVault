// CineVault OS — Collections & Franchises API Client Module (CAT-2)
// Handles fetching, creating, and deleting user-curated and franchise collections.

import { apiFetch } from "./client";
import { CollectionItem, CreateCollectionPayload } from "./types";

export async function getCollections(): Promise<CollectionItem[]> {
  return await apiFetch<CollectionItem[]>("/v1/personal/collections");
}

export async function createCollection(
  payload: CreateCollectionPayload
): Promise<CollectionItem> {
  return await apiFetch<CollectionItem>("/v1/personal/collections", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteCollection(id: string): Promise<void> {
  await apiFetch(`/v1/personal/collections/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}
