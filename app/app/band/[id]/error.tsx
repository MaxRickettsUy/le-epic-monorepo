"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";

export default function BandError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="flex flex-col items-start gap-[1rem] p-[1rem]">
      <h1 className="text-4xl">Something went wrong</h1>
      <p className="text-muted-foreground">This band couldn&apos;t be loaded.</p>
      <Button onClick={reset}>Try again</Button>
    </main>
  );
}
