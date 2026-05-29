import Link from "next/link";
import { Button } from "./ui/button";

/**
 * Prev/Next pager driven by the backend's `next`/`prev` page numbers. Preserves
 * the current search params (facets, sort) and only swaps `page`. Renders
 * nothing when there is a single page.
 */
export function Pagination({
  basePath,
  params,
  prev,
  next,
}: {
  basePath: string;
  /** Current search params to carry across page changes (page is overridden). */
  params: Record<string, string | undefined>;
  prev: number | null;
  next: number | null;
}) {
  if (prev == null && next == null) return null;

  const href = (page: number) => {
    const p = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v && k !== "page") p.set(k, v);
    }
    p.set("page", String(page));
    return `${basePath}?${p.toString()}`;
  };

  return (
    <nav className="flex items-center justify-center gap-3" aria-label="Pagination">
      <Button variant="outline" size="sm" disabled={prev == null} asChild={prev != null}>
        {prev != null ? <Link href={href(prev)}>← Previous</Link> : <span>← Previous</span>}
      </Button>
      <Button variant="outline" size="sm" disabled={next == null} asChild={next != null}>
        {next != null ? <Link href={href(next)}>Next →</Link> : <span>Next →</span>}
      </Button>
    </nav>
  );
}
