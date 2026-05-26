import Link from "next/link";
import { Header } from "@/components/ui/header";
import { Button } from "@/components/ui/button";

export default function ReleaseNotFound() {
  return (
    <main className="flex flex-col pb-[1rem]">
      <Header />
      <div className="flex flex-col items-start gap-[1rem] p-[1rem]">
        <h1 className="text-4xl">Release not found</h1>
        <p className="text-muted-foreground">
          We couldn&apos;t find the release you were looking for.
        </p>
        <Button asChild>
          <Link href="/">Back to all bands</Link>
        </Button>
      </div>
    </main>
  );
}
