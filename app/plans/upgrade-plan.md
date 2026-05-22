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

## Phase 2 — API & persistence (2–4 days, pick one path)

**Decision needed:** does this app continue to depend on an external backend, or should Next own the data?

- **Option A — Keep external backend.** Delete `app/api/**` stubs. Document the contract (`docs/api-contract.md`). Add zod schemas in `lib/schemas/` and validate every response at the boundary; surface parse failures via `error.tsx`.
- **Option B — Own the data in Next + Postgres (recommended for a self-contained app).**
  - Add Supabase (Postgres + RLS) or Drizzle + Neon. Supabase fits well given the available MCP tooling and shadcn/Radix stack.
  - Tables: `bands`, `releases`, `members`, `tracks`, `reviews`, `users`. Snake_case columns already match the TS types (`band_picture`, `band_id`, etc.).
  - Move reads to Server Components calling the DB directly; move writes to Server Actions (`'use server'`).
  - Replace `app/api/{home,band,release}/route.ts` with either nothing (if Server Actions cover it) or proper REST handlers if a public JSON API is desired.
  - Migrations live in `supabase/migrations/` (or `drizzle/`). Seed script for dev.

Deliverables: one source of truth, typed end-to-end, no client-side fetches to a different origin.

## Phase 3 — Forms & validation (1 day)

Goal: replace the bespoke `useState + lodash.debounce` pattern with the installed-but-unused zod, plus `react-hook-form`.

- Add `react-hook-form` + `@hookform/resolvers`.
- Define zod schemas for `Band`, `Release`, `Member`, `Track` in `lib/schemas/`.
- Refactor `app/create/band`, `app/create/release`, `app/edit/band`, `app/edit/release` to use `useForm({ resolver: zodResolver(schema) })`.
- Submit via Server Actions (Phase 2 Option B) or typed fetch helpers (Option A). Use `useFormStatus` for pending UI; `useFormState` (or RHF) for field errors.
- Drop the `typing` boolean + debounced submit-disable hack. Validation handles it.
- Remove `lodash` from `dependencies` once `_.debounce` calls are gone (saves ~70 KB).
- Bug to fix in pass: `app/create/release/page.tsx` imports `useRouter` from `next/router` (Pages Router) — should be `next/navigation`. Also calls `redirect()` inside a `.then` callback, which won't work; use Server Action redirect or `router.push`.

Deliverables: typed forms with inline errors, no manual debounce, smaller bundle.

## Phase 4 — UI/UX polish (1–2 days)

- Replace `<img>`-style band/release art with `next/image`. Add the real image host(s) to `next.config.mjs` `remotePatterns` (currently only `loremflickr.com`).
- Build real skeleton components (`components/ui/skeleton.tsx`) for loading states added in Phase 1.
- Implement the empty tabs on `app/release/[id]` (lineup, reviews, other) or hide them until backed by data.
- Implement `MemberTable` data path — `app/band/[id]/page.tsx` currently overrides `members: []` after fetch; either remove the tab or wire members through.
- Implement `app/recent-additions.tsx` and `app/recent-updates.tsx` (they exist but aren't rendered).
- Dark mode: `tailwind.config.ts` already has `darkMode: ["class"]` and CSS vars are defined; add a `ThemeProvider` (e.g. `next-themes`) and a toggle in `components/ui/header.tsx`.
- Accessibility audit: focus rings on `Link`/`Button` combos, `alt` text on images, semantic landmarks (`<nav>`, `<main>`).

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

1. Is there a real backend at `:8000` to keep (Option A), or should we own data in Next (Option B)?
2. Is this meant to be public-read / auth-gated-write (Metal Archives style), or fully private?
3. Where will band/release art be hosted? Needed to configure `next/image` remote patterns.
4. Target deployment (Vercel? self-host?) — affects edge vs. node runtime choices.
