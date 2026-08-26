// CineVault OS — Collections & Franchises API Client Module (CAT-2)
// Handles fetching, creating, and deleting user-curated and franchise collections.

import { apiFetch } from "./client";
import { CollectionItem, CollectionDetail, CreateCollectionPayload } from "./types";

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

// A collection could previously be created and deleted but never actually
// populated or viewed -- personal.user_list_item existed on the backend
// but nothing exposed adding/removing/listing items within one.

export async function getCollectionDetail(id: string): Promise<CollectionDetail> {
  return await apiFetch<CollectionDetail>(`/v1/personal/collections/${encodeURIComponent(id)}`);
}

export async function addCollectionItem(
  collectionId: string,
  titleId: string,
  notes?: string
): Promise<CollectionDetail> {
  return await apiFetch<CollectionDetail>(
    `/v1/personal/collections/${encodeURIComponent(collectionId)}/items`,
    {
      method: "POST",
      body: JSON.stringify({ title_id: titleId, notes }),
    }
  );
}

export async function removeCollectionItem(collectionId: string, titleId: string): Promise<void> {
  await apiFetch(
    `/v1/personal/collections/${encodeURIComponent(collectionId)}/items/${encodeURIComponent(titleId)}`,
    { method: "DELETE" }
  );
}
