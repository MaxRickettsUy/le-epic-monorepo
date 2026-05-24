import { Separator } from "@/components/ui/separator";
import Link from "next/link";
import { listBands } from "@/lib/api";
import { Header } from "@/components/ui/header";
import { Button } from "@/components/ui/button";

// Catalog data is served from the backend at request time; don't prerender at build.
export const dynamic = "force-dynamic";

export default async function Home() {
  const { bands } = await listBands();

  return (
    <main className="flex flex-col py-[1rem]">
      <Header />
      <div className="w-full py-[1rem]">
        <Separator />
      </div>
      <div className="flex flex-col gap-2 p-[1rem] md:flex-row">
        <div className="flex flex-col">
          {bands.map((band) => (
            <Button key={band.id} variant="ghost" asChild>
              <Link className="hover:underline" href={`/band/${band.id}`}>
                {band.name}
              </Link>
            </Button>
          ))}
        </div>
      </div>
    </main>
  );
}
