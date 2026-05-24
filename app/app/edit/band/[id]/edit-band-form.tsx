"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { countries } from "@/lib/const";
import { Header } from "@/components/ui/header";
import { updateBandAction } from "@/app/actions";
import type { Band } from "@/lib/types";
import type { BandCreateInput } from "@/lib/api";

export const EditBandForm = ({ band }: { band: Band }) => {
  const [form, setForm] = useState<BandCreateInput>({
    name: band.name,
    status: band.status,
    location: band.location,
    country: band.country,
    label: band.label,
    band_picture: band.band_picture ?? null,
  });
  const [pending, setPending] = useState(false);

  const set = (key: keyof BandCreateInput, value: string) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const disabled = pending || form.name.trim() === "";

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    try {
      await updateBandAction(band.id, form);
    } finally {
      setPending(false);
    }
  };

  return (
    <main className="flex-col py-[1rem]">
      <Header />
      <div className="w-full py-[1rem]">
        <Separator />
      </div>
      <div className="flex flex-col gap-[1rem] p-[1rem]">
        <form className="flex flex-col gap-[1rem]" onSubmit={onSubmit}>
          <span className="text-4xl">Edit Band</span>
          <Input
            value={form.name}
            onChange={(e) => set("name", e.target.value)}
            type="text"
            placeholder="Name"
          />
          <Select value={form.country} onValueChange={(c) => set("country", c)}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Country" />
            </SelectTrigger>
            <SelectContent>
              {countries.map((c) => (
                <SelectItem key={c.code} value={c.code}>
                  {c.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Input
            value={form.location}
            onChange={(e) => set("location", e.target.value)}
            type="text"
            placeholder="City, State"
          />
          <Input
            value={form.label}
            onChange={(e) => set("label", e.target.value)}
            type="text"
            placeholder="Label"
          />
          <Select value={form.status} onValueChange={(s) => set("status", s)}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="unknown">Unknown</SelectItem>
              <SelectItem value="on-hold">On Hold</SelectItem>
              <SelectItem value="split-up">Split Up</SelectItem>
            </SelectContent>
          </Select>
          <Button type="submit" disabled={disabled}>
            Submit
          </Button>
        </form>
      </div>
    </main>
  );
};
