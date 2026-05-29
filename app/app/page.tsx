import { listBands } from "@/lib/api";
import { Header } from "@/components/ui/header";
import { BandCard } from "@/components/BandCard";

// Catalog data is served from the backend at request time; don't prerender at build.
export const dynamic = "force-dynamic";

export default async function Home() {
  // Backend caps the page at `bands_per_page` (10); `recent` orders by created_at desc.
  const { bands } = await listBands({ page: 1, sort: "recent" });

  return (
    <main className="flex flex-col pb-[1rem]">
      <Header />
      <div className="p-[1rem]">
        <h2 className="mb-4 text-lg font-semibold tracking-tight">Recently added</h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          {bands.map((band) => (
            <BandCard key={band.id} band={band} />
          ))}
        </div>
      </div>
    </main>
  );
}
