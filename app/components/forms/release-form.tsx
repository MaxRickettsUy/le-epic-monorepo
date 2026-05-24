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
import { Header } from "@/components/ui/header";
import { releaseTypes } from "@/lib/const";
import type { ReleaseCreateInput } from "@/lib/api";

const START_YEAR = 1982;
const END_YEAR = new Date().getFullYear();

export const ReleaseForm = ({
  title,
  defaultValues,
  onSubmit,
}: {
  title: string;
  defaultValues?: Partial<ReleaseCreateInput>;
  onSubmit: (input: ReleaseCreateInput) => Promise<void>;
}) => {
  const [form, setForm] = useState<ReleaseCreateInput>({
    name: defaultValues?.name ?? "",
    label: defaultValues?.label ?? null,
    release_type: defaultValues?.release_type ?? null,
    year: defaultValues?.year ?? null,
    length: defaultValues?.length ?? null,
    art: defaultValues?.art ?? null,
  });
  const [pending, setPending] = useState(false);

  const disabled = pending || form.name.trim() === "";

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    try {
      await onSubmit(form);
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
        <form className="flex flex-col gap-[1rem]" onSubmit={submit}>
          <span className="text-4xl">{title}</span>
          <Input
            value={form.name}
            onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
            type="text"
            placeholder="Name"
          />
          <Select
            value={form.year ? String(form.year) : undefined}
            onValueChange={(y) => setForm((p) => ({ ...p, year: Number(y) }))}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Year" />
            </SelectTrigger>
            <SelectContent>
              {Array.from({ length: END_YEAR - START_YEAR + 1 }, (_, i) => {
                const year = START_YEAR + i;
                return (
                  <SelectItem key={year} value={String(year)}>
                    {year}
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>
          <Select
            value={form.release_type ?? undefined}
            onValueChange={(t) => setForm((p) => ({ ...p, release_type: t }))}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Release Type" />
            </SelectTrigger>
            <SelectContent>
              {releaseTypes.map((o) => (
                <SelectItem key={o.value} value={o.value}>
                  {o.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Input
            value={form.label ?? ""}
            onChange={(e) => setForm((p) => ({ ...p, label: e.target.value || null }))}
            type="text"
            placeholder="Label"
          />
          <Button type="submit" disabled={disabled}>
            Submit
          </Button>
        </form>
      </div>
    </main>
  );
};
