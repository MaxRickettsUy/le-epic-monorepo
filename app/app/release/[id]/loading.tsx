import { Header } from "@/components/ui/header";
import { Separator } from "@/components/ui/separator";

export default function Loading() {
  return (
    <main className="flex-col py-[1rem]">
      <Header />
      <div className="w-full py-[1rem]">
        <Separator />
      </div>
      <div className="flex flex-col gap-[1rem] p-4 md:flex-row">
        <div className="h-[420px] w-[290px] animate-pulse rounded-md bg-muted" />
        <div className="flex w-full flex-col gap-3 p-4">
          <div className="h-8 w-32 animate-pulse rounded bg-muted" />
          <div className="h-64 w-full animate-pulse rounded bg-muted" />
        </div>
      </div>
    </main>
  );
}
