import type { SearchResults } from "@/lib/types";
import { searchResultsSchema } from "@/lib/schemas";
import { apiFetch } from "./client";

/**
 * Catalogue search across band and album names (`GET /search/?q=`). The backend
 * requires a non-empty query, so callers should guard against blank input.
 */
export function search(query: string): Promise<SearchResults> {
  return apiFetch(`/search/?q=${encodeURIComponent(query)}`, searchResultsSchema, {
    next: { revalidate: 60 },
  });
}
