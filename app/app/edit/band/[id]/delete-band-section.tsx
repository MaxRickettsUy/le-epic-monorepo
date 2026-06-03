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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { deleteBandAction } from "@/app/actions";

const PRESET_CATEGORIES = ["off-genre", "not a band", "duplicate", "low quality", "other"] as const;

type PresetCategory = (typeof PRESET_CATEGORIES)[number];

export const DeleteBandSection = ({ bandId, bandName }: { bandId: number; bandName: string }) => {
  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState<PresetCategory>("off-genre");
  const [detail, setDetail] = useState("");
  const [blacklist, setBlacklist] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const REASON_MAX = 500;
  const detailMax = category === "other" ? REASON_MAX : REASON_MAX - (category.length + 2);

  const composedReason = (() => {
    const d = detail.trim().slice(0, detailMax);
    if (category === "other") return d || null;
    return d ? `${category}: ${d}` : category;
  })();

  const onDelete = () => {
    setError(null);
    startTransition(async () => {
      try {
        await deleteBandAction(bandId, {
          blacklist,
          reason: composedReason,
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
      setCategory("off-genre");
      setDetail("");
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
            <div className="flex flex-col gap-2">
              <div className="flex flex-col gap-1">
                <Label htmlFor="delete-reason-category">
                  Reason (stored on the blacklist entry)
                </Label>
                <Select
                  value={category}
                  onValueChange={(v) => setCategory(v as PresetCategory)}
                  disabled={isPending}
                >
                  <SelectTrigger id="delete-reason-category">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PRESET_CATEGORIES.map((c) => (
                      <SelectItem key={c} value={c}>
                        {c}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex flex-col gap-1">
                <Label htmlFor="delete-reason-detail" className="text-muted-foreground">
                  Detail (optional)
                </Label>
                <Input
                  id="delete-reason-detail"
                  value={detail}
                  onChange={(e) => setDetail(e.target.value.slice(0, detailMax))}
                  maxLength={detailMax}
                  placeholder={
                    category === "off-genre"
                      ? "e.g. sludge — MB tags say grindcore, not hardcore punk"
                      : category === "other"
                        ? "describe the reason"
                        : "optional extra context"
                  }
                  disabled={isPending}
                />
              </div>
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
