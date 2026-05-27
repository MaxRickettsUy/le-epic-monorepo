// Public type surface for API payloads. The shapes are defined once as zod
// schemas in ./schemas (validated at the network boundary) and re-exported
// here so existing `@/lib/types` imports keep working. See ../backend/app/schemas.py.

export type {
  BandStatus,
  Member,
  Track,
  Release,
  BandSummary,
  SimilarBand,
  ReleaseDetail,
  BandListItem,
  Band,
  BandList,
  MutationResult,
  BandSearchItem,
  AlbumSearchItem,
  SearchResults,
} from "./schemas";

// Reviews are out of MVP and not returned by the backend yet, so these have no
// schema counterpart. They describe the intended shape for Phase 4 UI work.
export interface User {
  name: string;
}

export interface Review {
  author: User;
  release: import("./schemas").Release;
  date: string;
}
