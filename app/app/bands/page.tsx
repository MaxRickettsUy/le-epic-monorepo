import Link from "next/link";
import type { Metadata } from "next";
import { listBands, listGenres, listCountries, type BandListFilters } from "@/lib/api";
import { Header } from "@/components/ui/header";
import { BandCard } from "@/components/BandCard";
import { Pagination } from "@/components/Pagination";
import { Badge } from "@/components/ui/badge";

// Listing depends on the live catalogue and the active facets; never prerender.
export const dynamic = "force-dynamic";

export const metadata: Metadata = { title: "Browse bands" };

const LETTERS = ["#", ..."ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("")];
const FACET_KEYS = ["sort", "genre", "country", "letter"] as const;

type Facets = Partial<Record<(typeof FACET_KEYS)[number], string>>;

interface PageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

function first(v?: string | string[]): string | undefined {
  const s = Array.isArray(v) ? v[0] : v;
  return s && s.length > 0 ? s : undefined;
}

/** A `/bands` URL with one facet overridden (or cleared with `null`); resets to page 1. */
function facetHref(active: Facets, key: string, value: string | null): string {
  const p = new URLSearchParams();
  for (const k of FACET_KEYS) {
    const v = k === key ? value : active[k];
    if (v) p.set(k, v);
  }
  const qs = p.toString();
  return qs ? `/bands?${qs}` : "/bands";
}

export default async function BandsPage({ searchParams }: PageProps) {
  const sp = await searchParams;

  const sortRaw = first(sp.sort);
  const sort: "name" | "recent" = sortRaw === "recent" ? "recent" : "name";
  const genre = first(sp.genre);
  const country = first(sp.country);
  // Guard the letter facet so bad input doesn't reach the backend (which 422s).
  const letterRaw = first(sp.letter);
  const letter = letterRaw === "#" || /^[A-Za-z]$/.test(letterRaw ?? "") ? letterRaw : undefined;
  const page = Math.max(1, Number(first(sp.page)) || 1);

  const active: Facets = { sort: sort === "name" ? undefined : sort, genre, country, letter };
  const hasFacets = Boolean(genre || country || letter);

  const filters: BandListFilters = { page, sort, genre, country, letter };
  const [{ bands, next, prev }, genres, countries] = await Promise.all([
    listBands(filters),
    listGenres(),
    listCountries(),
  ]);

  return (
    <main className="flex flex-col pb-[1rem]">
      <Header />
      <div className="flex flex-col gap-6 p-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h1 className="text-lg font-semibold tracking-tight">Browse bands</h1>
          {hasFacets && (
            <Link href="/bands" className="text-sm text-muted-foreground hover:underline">
              Clear filters
            </Link>
          )}
        </div>

        {/* Sort */}
        <div className="flex items-center gap-2 text-sm">
          <span className="text-muted-foreground">Sort</span>
          {(["name", "recent"] as const).map((s) => (
            <Link
              key={s}
              href={facetHref(active, "sort", s === "name" ? null : s)}
              className={`rounded-md px-2 py-1 ${
                sort === s ? "bg-primary text-primary-foreground" : "hover:bg-muted"
              }`}
            >
              {s === "name" ? "A–Z" : "Recently added"}
            </Link>
          ))}
        </div>

        {/* Alphabetical */}
        <div className="flex flex-wrap gap-1">
          {LETTERS.map((l) => {
            const isActive = letter === l;
            return (
              <Link
                key={l}
                href={facetHref(active, "letter", isActive ? null : l)}
                className={`rounded px-2 py-1 text-sm ${
                  isActive ? "bg-primary text-primary-foreground" : "hover:bg-muted"
                }`}
              >
                {l}
              </Link>
            );
          })}
        </div>

        {/* Genre */}
        {genres.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {genres.map((g) => {
              const isActive = genre === g.slug;
              return (
                <Link key={g.slug} href={facetHref(active, "genre", isActive ? null : g.slug)}>
                  <Badge variant={isActive ? "default" : "secondary"}>{g.name}</Badge>
                </Link>
              );
            })}
          </div>
        )}

        {/* Country — native select in a GET form keeps the page server-rendered. */}
        {countries.length > 0 && (
          <form method="get" action="/bands" className="flex items-center gap-2 text-sm">
            {active.sort && <input type="hidden" name="sort" value={active.sort} />}
            {genre && <input type="hidden" name="genre" value={genre} />}
            {letter && <input type="hidden" name="letter" value={letter} />}
            <label htmlFor="country" className="text-muted-foreground">
              Country
            </label>
            <select
              id="country"
              name="country"
              defaultValue={country ?? ""}
              className="rounded-md border bg-background px-2 py-1"
            >
              <option value="">All countries</option>
              {countries.map((c) => (
                <option key={c.country} value={c.country}>
                  {c.country} ({c.count})
                </option>
              ))}
            </select>
            <button type="submit" className="rounded-md border px-2 py-1 hover:bg-muted">
              Apply
            </button>
          </form>
        )}

        {/* Results */}
        {bands.length === 0 ? (
          <p className="text-muted-foreground">No bands match these filters.</p>
        ) : (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
            {bands.map((band) => (
              <BandCard key={band.id} band={band} />
            ))}
          </div>
        )}

        <Pagination
          basePath="/bands"
          params={{ sort: active.sort, genre, country, letter }}
          prev={prev}
          next={next}
        />
      </div>
    </main>
  );
}
