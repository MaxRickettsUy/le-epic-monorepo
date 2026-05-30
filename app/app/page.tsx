import Link from "next/link";
import { listBands, listGenres, listReleases } from "@/lib/api";
import { Header } from "@/components/ui/header";
import { BandCard } from "@/components/BandCard";
import { AlbumCard } from "@/components/AlbumCard";
import { Badge } from "@/components/ui/badge";

// Catalog data is served from the backend at request time; don't prerender at build.
export const dynamic = "force-dynamic";

export default async function Home() {
  // Backend caps each list at its respective per-page setting (10); `recent`
  // orders by created_at desc.
  const [{ bands }, { releases }, genres] = await Promise.all([
    listBands({ page: 1, sort: "recent" }),
    listReleases({ page: 1, sort: "recent" }),
    listGenres(),
  ]);

  return (
    <main className="flex flex-col gap-8 pb-[1rem]">
      <Header />

      <section className="px-[1rem]">
        <h2 className="mb-4 text-lg font-semibold tracking-tight">Recently added bands</h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          {bands.map((band) => (
            <BandCard key={band.id} band={band} />
          ))}
        </div>
      </section>

      {releases.length > 0 && (
        <section className="px-[1rem]">
          <h2 className="mb-4 text-lg font-semibold tracking-tight">Recent releases</h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
            {releases.map((release) => (
              <AlbumCard key={release.id} release={release} />
            ))}
          </div>
        </section>
      )}

      {genres.length > 0 && (
        <section className="px-[1rem]">
          <h2 className="mb-4 text-lg font-semibold tracking-tight">Browse by genre</h2>
          <div className="flex flex-wrap gap-1.5">
            {genres.map((g) => (
              <Link key={g.slug} href={`/bands?genre=${encodeURIComponent(g.slug)}`}>
                <Badge variant="secondary" className="hover:bg-secondary/80">
                  {g.name}
                </Badge>
              </Link>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
