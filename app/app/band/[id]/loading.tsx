import { Header } from "@/components/ui/header";
import { Skeleton } from "@/components/ui/skeleton";

export default function Loading() {
  return (
    <main className="flex flex-col pb-[1rem]">
      <Header />
      <div className="flex flex-col gap-[1rem] p-4 md:flex-row" aria-busy="true">
        <Skeleton className="h-[420px] w-[290px]" />
        <div className="flex w-full flex-col gap-3 p-4">
          <Skeleton className="h-8 w-40" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    </main>
  );
}
