# Upgrade Plan — le-epic-app

A staged plan for modernizing this Next.js 15 / React 19 band & release catalog. Each phase is independently shippable; later phases assume earlier ones landed.

## Current state (baseline)

- **Stack:** Next.js 15.5 (App Router, Turbopack), React 19, TypeScript 5, Tailwind 3, shadcn/ui + Radix, lodash, zod (installed, unused), `@faker-js/faker` in deps (used only in a leftover import).
- **Data layer:** No DB. App expects an external HTTP API at `NEXT_PUBLIC_API_URI:NEXT_PUBLIC_API_PORT` (defaults to `http://127.0.0.1:8000`). All `/app/api/*` route handlers are commented-out stubs.
- **Fetching:** Every page is `'use client'` and uses `useEffect` + `fetch` against env-derived URLs. No loading states, no error states, no caching, no Suspense.
- **Routing model:** Detail pages use query strings (`/band?id=…`, `/release?id=…`) instead of dynamic segments.
- **Forms:** Hand-rolled `useState` + `lodash.debounce` per input. No `react-hook-form`, no zod validation despite zod being installed.
- **Quality gates:** Only `next lint` with `next/core-web-vitals`. No Prettier, no typecheck script, no tests, no CI.
- **Hygiene:** Debug `border border-red-500` left on band/release pages. `console.log` calls in render. Large blocks of commented-out code. Dead routes in `app/api`. `Album` interface commented out but referenced in stubs. `/edit/release/page.tsx` exists but not inspected — likely the same pattern. `Image` configured only for `loremflickr.com`. Default `<title>` ("Create Next App"). `.env.production` empty.
- **Security/perf:** Public API base in `NEXT_PUBLIC_*` (fine for public APIs, but no auth layer). No rate limiting, no auth, no CSP, no headers config.

## Phase 0 — Stabilize (≈ ½ day)

Goal: clean baseline before any architectural work. No behavior changes.

- Remove debug `border border-red-500` classes from `app/band/page.tsx` and `app/release/page.tsx`.
- Strip `console.log` from render bodies.
- Delete commented-out blocks (`app/api/**/route.ts` stubs, the `RecentAdditions/Updates/Reviews` blocks in `app/release/page.tsx`, the unused `Album` interface in `lib/types.ts`).
- Either delete `app/api/**` routes entirely (recommended — they're empty) or implement them in Phase 2.
- Set real `metadata` in `app/layout.tsx` (title, description, viewport).
- Add scripts: `"typecheck": "tsc --noEmit"`, `"format": "prettier --write ."`.
- Add Prettier + `.prettierrc` + `.prettierignore`. Add `eslint-config-prettier`.
- Add a basic CI workflow (`.github/workflows/ci.yml`) running `lint`, `typecheck`, `build` on PRs.

Deliverables: green CI on a clean baseline.

## Phase 1 — Routing & data-fetching modernization (1–2 days)

Goal: use App Router primitives properly. Move data fetching off the client.

- Convert query-string routes to dynamic segments:
  - `app/band/page.tsx` (uses `?id=`) → `app/band/[id]/page.tsx`
  - `app/release/page.tsx` (uses `?id=`) → `app/release/[id]/page.tsx`
  - `app/edit/band/page.tsx` (uses `?id=`) → `app/edit/band/[id]/page.tsx`
  - `app/edit/release/page.tsx` → `app/edit/release/[id]/page.tsx`
  - `app/create/release/page.tsx` (uses `?band_id=`) → `app/create/release/[bandId]/page.tsx`
- Make pages Server Components by default; fetch on the server using `fetch` with explicit `cache` / `next.revalidate` per route.
- Create a typed server-side data layer in `lib/api/` (`getBand(id)`, `listBands()`, `getRelease(id)`, `createBand`, `createRelease`). Centralize base URL; read from `process.env.API_URL` (server) instead of `NEXT_PUBLIC_*` so the API host isn't shipped to the browser unless it must be.
- Add `loading.tsx` (Suspense skeletons) and `error.tsx` boundaries under `app/band/[id]`, `app/release/[id]`, and the root.
- Add `not-found.tsx` for unknown ids.
- Keep small interactive islands as `'use client'` (tabs, selects, form inputs only).

Deliverables: shareable URLs are stable, SSR works, network panel shows server-rendered HTML.

## Phase 2 — API & persistence (2–4 days, pick one path) — ✅ DONE (Option A)

**Decision:** Keep the external FastAPI + Postgres backend (`backend/`). It was deliberately resurrected and Phase 1 already built the `lib/api/` layer against it, so Next stays a pure client and does not own data.

- **Option A — Keep external backend.** ✅ `app/api/**` stubs already deleted. Contract documented in `docs/api-contract.md`. Zod schemas added in `lib/schemas/` (now the single source of truth — `lib/types.ts` re-exports the inferred types). Every response is validated at the boundary in `lib/api/client.ts`; a 2xx mismatch throws `ApiParseError`, which surfaces via the existing `error.tsx` boundaries.
- **Option B — Own the data in Next + Postgres (recommended for a self-contained app).**
  - Add Supabase (Postgres + RLS) or Drizzle + Neon. Supabase fits well given the available MCP tooling and shadcn/Radix stack.
  - Tables: `bands`, `releases`, `members`, `tracks`, `reviews`, `users`. Snake_case columns already match the TS types (`band_picture`, `band_id`, etc.).
  - Move reads to Server Components calling the DB directly; move writes to Server Actions (`'use server'`).
  - Replace `app/api/{home,band,release}/route.ts` with either nothing (if Server Actions cover it) or proper REST handlers if a public JSON API is desired.
  - Migrations live in `supabase/migrations/` (or `drizzle/`). Seed script for dev.

Deliverables: one source of truth, typed end-to-end, no client-side fetches to a different origin.

## Phase 3 — Forms & validation (1 day) — ✅ DONE (TanStack Form)

Goal: replace the bespoke `useState` form state with zod validation + a form library.

**Decision:** Used `@tanstack/react-form` instead of `react-hook-form`/`@hookform/resolvers`. TanStack validates a Standard Schema (zod 3.24+) directly, so no separate resolver package is needed. Bumped `zod` to `^3.25` for Standard Schema support.

- ✅ Added `@tanstack/react-form` + `@radix-ui/react-label`.
- ✅ Added form-input zod schemas (`bandFormSchema`, `releaseFormSchema` + inferred types) to `lib/schemas/index.ts`, kept separate from the response-contract schemas (no server-assigned fields, stricter required rules).
- ✅ Refactored to TanStack `useForm({ validators: { onChange: schema } })`:
  - New shared `components/forms/band-form.tsx` used by `app/create/band` and `app/edit/band/[id]`.
  - Existing shared `components/forms/release-form.tsx` (covers create + edit release) converted off `useState`.
  - Inline field errors via `components/forms/field-error.tsx` (touched-only); pending/disabled via `form.Subscribe` on `canSubmit`/`isSubmitting`.
- ✅ Submit still goes through the Phase-1 Server Actions in `app/actions.ts` (Option A typed fetch helpers).
- ✅ Removed `lodash` + `@types/lodash` from `package.json` (already unused in source after Phase 1).
- N/A: the `next/router` import bug and `.then`-redirect were already fixed in Phase 1 (release create uses `useParams` + a Server Action).

Deliverables: typed forms with inline errors, no manual form-state plumbing, smaller bundle. CI green (lint, typecheck, build).

## Phase 4 — UI/UX polish (1–2 days) — ✅ DONE

- ✅ Replaced the placeholder art `<div>` in `components/TopSection.tsx` with `next/image` (initials placeholder retained as the no-art fallback). Release art now flows through via `release.art`. `next.config.mjs` `remotePatterns` keeps `loremflickr.com` and adds a permissive `https://**` host until the art CDN is finalized (open question #3).
- ✅ Added `components/ui/skeleton.tsx` and adopted it in the `band/[id]` and `release/[id]` `loading.tsx` (with `aria-busy`).
- N/A: the empty lineup/reviews/other tabs on `app/release/[id]` were already removed in an earlier phase — only the backed Tracks tab remains.
- ✅ `MemberTable` data path is wired (`band.members` flows through). Dropped the unbacked "Other Bands" column (no field in the contract) and added an empty state; members are always `[]` in the MVP.
- N/A: `app/recent-additions.tsx` / `app/recent-updates.tsx` no longer exist (removed in an earlier phase).
- ✅ Dark mode: added `next-themes`, a `components/theme-provider.tsx` wrapper in `app/layout.tsx` (`attribute="class"`, system default, `suppressHydrationWarning` on `<html>`), and a `components/ui/theme-toggle.tsx` (lucide sun/moon) in the header.
- ✅ Accessibility: header is now `<header>` + `<nav aria-label="Primary">`; search input has an `sr-only` label; `next/image` has `alt` text and the fallback uses `role="img"` + `aria-label`. `Button`/`Input` already ship `focus-visible` rings.

## Phase 5 — Auth & authorization (1–2 days, only if Phase 2 Option B)

- Supabase Auth (email/OTP or OAuth) or Auth.js.
- Gate `/create/*` and `/edit/*` routes via middleware.
- RLS policies so users can only edit their own contributions; reads stay public.
- Add an `audit_log` table for edits if this is meant to feel like Metal Archives.

## Phase 6 — Testing & observability (1 day)

- Unit: Vitest + React Testing Library for components (`TopSection`, form components, tables).
- E2E: Playwright for the golden paths — view band, view release, create band, create release.
- Wire test scripts into CI from Phase 0.
- Add Sentry (or equivalent) for error tracking; instrument Server Actions.
- Add `@next/bundle-analyzer` and check for regressions after lodash removal.

## Phase 7 — Dependency & framework hygiene (ongoing)

- Pin `next` and `eslint-config-next` to the same minor version (currently `^15.5.18` vs `15.0.1`).
- Upgrade ESLint to v9 + flat config (current is v8).
- Consider Tailwind v4 once the shadcn ecosystem catches up (low priority).
- Move `@faker-js/faker` out of `dependencies` (only used in deleted stubs) — drop it entirely after Phase 0.
- Audit `package.json` `overrides` block; the `postcss` override was likely a workaround that may no longer be needed.

## Suggested sequencing

A pragmatic order if you want incremental value: **Phase 0 → 1 → 3 → 2 → 4 → 5 → 6 → 7**. Phase 3 before Phase 2 is fine because form validation can run client-side first, then plug into Server Actions when persistence lands.

## Open questions for the owner

1. ~~Is there a real backend at `:8000` to keep (Option A), or should we own data in Next (Option B)?~~ **Resolved:** Option A chosen (see Phase 2). The contract is finalized in `docs/api-contract.md` and the canonical zod schemas live in `lib/schemas/` (re-exported as inferred types via `lib/types.ts`).
2. Is this meant to be public-read / auth-gated-write (Metal Archives style), or fully private?
3. Where will band/release art be hosted? Needed to configure `next/image` remote patterns.
4. Target deployment (Vercel? self-host?) — affects edge vs. node runtime choices.
