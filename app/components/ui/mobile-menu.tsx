"use client";

import { useEffect, useId, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import { Button } from "./button";
import { Input } from "./input";

export function MobileMenu() {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const pathname = usePathname();
  const firstFieldRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    firstFieldRef.current?.focus();
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [open]);

  return (
    <>
      <Button
        type="button"
        variant="outline"
        size="icon"
        aria-label={open ? "Close menu" : "Open menu"}
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((v) => !v)}
      >
        {open ? <X className="h-5 w-5" aria-hidden /> : <Menu className="h-5 w-5" aria-hidden />}
      </Button>
      {open && (
        <div
          id={panelId}
          role="dialog"
          aria-modal="true"
          aria-label="Menu"
          className="fixed inset-x-0 bottom-0 top-14 z-40 flex flex-col bg-background px-[1rem] py-[1rem]"
        >
          <nav aria-label="Mobile" className="flex flex-col gap-4">
            <form action="/search" method="get" role="search">
              <label htmlFor="catalog-search-mobile" className="sr-only">
                Search the catalog
              </label>
              <Input
                ref={firstFieldRef}
                id="catalog-search-mobile"
                name="q"
                type="search"
                placeholder="Search bands & albums..."
              />
            </form>
            <Link href="/bands" className="text-lg font-medium hover:underline">
              Browse
            </Link>
          </nav>
        </div>
      )}
    </>
  );
}
