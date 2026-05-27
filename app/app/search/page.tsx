import Link from "next/link";
import type { Metadata } from "next";
import { search } from "@/lib/api";
import { Header } from "@/components/ui/header";

// Results depend on the live catalogue and the query string; never prerender.
export const dynamic = "force-dynamic";

interface PageProps {
  searchParams: Promise<{ q?: string }>;
}

export async function generateMetadata({ searchParams }: PageProps): Promise<Metadata> {
  const { q } = await searchParams;
  const term = q?.trim();
  return { title: term ? `Search: ${term}` : "Search" };
}

export default async function SearchPage({ searchParams }: PageProps) {
  const { q } = await searchParams;
  const term = q?.trim() ?? "";

  if (!term) {
    return (
      <main className="flex flex-col pb-[1rem]">
        <Header />
        <p className="p-4 text-muted-foreground">Type a band or album name to search.</p>
      </main>
    );
  }

  const { bands, albums } = await search(term);
  const empty = bands.length === 0 && albums.length === 0;

  return (
    <main className="flex flex-col pb-[1rem]">
      <Header />
      <div className="flex flex-col gap-8 p-4">
        <h1 className="text-lg font-semibold tracking-tight">
          Results for <span className="text-muted-foreground">&ldquo;{term}&rdquo;</span>
        </h1>

        {empty && (
          <p className="text-muted-foreground">No bands or albums match that search.</p>
        )}

        {bands.length > 0 && (
          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Bands
            </h2>
            <ul className="flex flex-col divide-y rounded-md border">
              {bands.map((band) => (
                <li key={band.id}>
                  <Link
                    href={`/band/${band.id}`}
                    className="flex items-baseline justify-between gap-4 px-4 py-3 hover:bg-muted"
                  >
                    <span className="font-medium">{band.name}</span>
                    <span className="truncate text-sm text-muted-foreground">
                      {band.location || band.country}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        )}

        {albums.length > 0 && (
          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Albums
            </h2>
            <ul className="flex flex-col divide-y rounded-md border">
              {albums.map((album) => (
                <li key={album.id}>
                  <Link
                    href={`/release/${album.id}`}
                    className="flex items-baseline justify-between gap-4 px-4 py-3 hover:bg-muted"
                  >
                    <span className="font-medium">{album.name}</span>
                    <span className="truncate text-sm text-muted-foreground">
                      {album.band_name}
                      {album.year ? ` · ${album.year}` : ""}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </main>
  );
}
