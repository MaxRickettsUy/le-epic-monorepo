import Link from "next/link";
import { Header } from "@/components/ui/header";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <main className="flex flex-col py-[1rem]">
      <Header />
      <div className="w-full py-[1rem]">
        <Separator />
      </div>
      <div className="flex flex-col items-start gap-[1rem] p-[1rem]">
        <h1 className="text-4xl">Page not found</h1>
        <p className="text-muted-foreground">This page doesn&apos;t exist.</p>
        <Button asChild>
          <Link href="/">Back home</Link>
        </Button>
      </div>
    </main>
  );
}
