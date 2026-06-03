"use client";

import { useState, useTransition } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { deleteBandAction } from "@/app/actions";

export const DeleteBandSection = ({ bandId, bandName }: { bandId: number; bandName: string }) => {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [blacklist, setBlacklist] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const onDelete = () => {
    setError(null);
    startTransition(async () => {
      try {
        await deleteBandAction(bandId, {
          blacklist,
          reason: reason.trim() || null,
        });
      } catch (e) {
        // Server actions throw a special redirect error on success — Next.js
        // marks it via the `digest` field, which is the documented contract
        // (the `.message` text isn't stable across versions).
        const digest =
          e instanceof Error ? (e as unknown as { digest?: unknown }).digest : undefined;
        if (typeof digest === "string" && digest.startsWith("NEXT_REDIRECT")) {
          return;
        }
        setError(e instanceof Error ? e.message : "Delete failed");
      }
    });
  };

  const onOpenChange = (next: boolean) => {
    if (isPending) return;
    setOpen(next);
    if (!next) {
      setReason("");
      setError(null);
    }
  };

  return (
    <section className="flex flex-col gap-3 rounded-md border border-destructive/40 p-4">
      <div className="flex flex-col gap-1">
        <h2 className="text-lg font-semibold text-destructive">Danger zone</h2>
        <p className="text-sm text-muted-foreground">
          Delete this band, its albums, tracks, and member links. By default the band&rsquo;s
          MusicBrainz ID is added to the blacklist so <code>seed.mb_dump</code> won&rsquo;t
          resurrect it on the next run.
        </p>
      </div>

      <div>
        <Button type="button" variant="destructive" onClick={() => setOpen(true)}>
          Delete band&hellip;
        </Button>
      </div>

      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete {bandName}?</DialogTitle>
            <DialogDescription>
              Permanently removes the band, its albums, tracks, and member links. This can&rsquo;t
              be undone.
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-3">
            <div className="flex flex-col gap-1">
              <Label htmlFor="delete-reason">
                Reason (optional, stored on the blacklist entry)
              </Label>
              <Input
                id="delete-reason"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                maxLength={500}
                placeholder="e.g. off-genre — MB tags say grindcore, not hardcore punk"
                disabled={isPending}
              />
            </div>

            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={blacklist}
                onChange={(e) => setBlacklist(e.target.checked)}
                disabled={isPending}
              />
              Blacklist the MBID so seeding won&rsquo;t bring it back
            </label>

            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button type="button" variant="destructive" onClick={onDelete} disabled={isPending}>
              {isPending ? "Deleting…" : "Confirm delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  );
};
