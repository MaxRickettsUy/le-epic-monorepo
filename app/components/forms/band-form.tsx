"use client";

import { useForm } from "@tanstack/react-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Header } from "@/components/ui/header";
import { FieldError } from "@/components/forms/field-error";
import { countries } from "@/lib/const";
import { bandFormSchema, type BandFormValues } from "@/lib/schemas";

const statuses: { value: BandFormValues["status"]; label: string }[] = [
  { value: "active", label: "Active" },
  { value: "unknown", label: "Unknown" },
  { value: "on-hold", label: "On Hold" },
  { value: "split-up", label: "Split Up" },
];

export const BandForm = ({
  title,
  defaultValues,
  onSubmit,
}: {
  title: string;
  defaultValues?: Partial<BandFormValues>;
  onSubmit: (input: BandFormValues) => Promise<void>;
}) => {
  const form = useForm({
    defaultValues: {
      name: defaultValues?.name ?? "",
      status: defaultValues?.status ?? "active",
      country: defaultValues?.country ?? "",
      location: defaultValues?.location ?? "",
      label: defaultValues?.label ?? "",
      band_picture: defaultValues?.band_picture ?? null,
      logo: defaultValues?.logo ?? null,
    } as BandFormValues,
    validators: { onChange: bandFormSchema },
    onSubmit: async ({ value }) => {
      await onSubmit(value);
    },
  });

  return (
    <main className="flex-col py-[1rem]">
      <Header />
      <div className="w-full py-[1rem]">
        <Separator />
      </div>
      <div className="flex flex-col gap-[1rem] p-[1rem]">
        <form
          className="flex flex-col gap-[1rem]"
          onSubmit={(e) => {
            e.preventDefault();
            e.stopPropagation();
            form.handleSubmit();
          }}
        >
          <span className="text-4xl">{title}</span>

          <form.Field name="name">
            {(field) => (
              <div className="flex flex-col gap-[0.5rem]">
                <Label htmlFor={field.name}>Name</Label>
                <Input
                  id={field.name}
                  name={field.name}
                  value={field.state.value}
                  onBlur={field.handleBlur}
                  onChange={(e) => field.handleChange(e.target.value)}
                  type="text"
                  placeholder="Name"
                />
                <FieldError meta={field.state.meta} show={form.state.submissionAttempts > 0} />
              </div>
            )}
          </form.Field>

          <form.Field name="country">
            {(field) => (
              <div className="flex flex-col gap-[0.5rem]">
                <Label htmlFor={field.name}>Country</Label>
                <Select value={field.state.value} onValueChange={field.handleChange}>
                  <SelectTrigger id={field.name} className="w-[180px]" onBlur={field.handleBlur}>
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
                <FieldError meta={field.state.meta} show={form.state.submissionAttempts > 0} />
              </div>
            )}
          </form.Field>

          <form.Field name="location">
            {(field) => (
              <div className="flex flex-col gap-[0.5rem]">
                <Label htmlFor={field.name}>Location</Label>
                <Input
                  id={field.name}
                  name={field.name}
                  value={field.state.value}
                  onBlur={field.handleBlur}
                  onChange={(e) => field.handleChange(e.target.value)}
                  type="text"
                  placeholder="City, State"
                />
                <FieldError meta={field.state.meta} show={form.state.submissionAttempts > 0} />
              </div>
            )}
          </form.Field>

          <form.Field name="label">
            {(field) => (
              <div className="flex flex-col gap-[0.5rem]">
                <Label htmlFor={field.name}>Label</Label>
                <Input
                  id={field.name}
                  name={field.name}
                  value={field.state.value}
                  onBlur={field.handleBlur}
                  onChange={(e) => field.handleChange(e.target.value)}
                  type="text"
                  placeholder="Label"
                />
                <FieldError meta={field.state.meta} show={form.state.submissionAttempts > 0} />
              </div>
            )}
          </form.Field>

          <form.Field name="logo">
            {(field) => (
              <div className="flex flex-col gap-[0.5rem]">
                <Label htmlFor={field.name}>Logo URL</Label>
                <Input
                  id={field.name}
                  name={field.name}
                  value={field.state.value ?? ""}
                  onBlur={field.handleBlur}
                  onChange={(e) => field.handleChange(e.target.value || null)}
                  type="url"
                  placeholder="https://…"
                />
                <FieldError meta={field.state.meta} show={form.state.submissionAttempts > 0} />
              </div>
            )}
          </form.Field>

          <form.Field name="status">
            {(field) => (
              <div className="flex flex-col gap-[0.5rem]">
                <Label htmlFor={field.name}>Status</Label>
                <Select
                  value={field.state.value}
                  onValueChange={(v) => field.handleChange(v as BandFormValues["status"])}
                >
                  <SelectTrigger id={field.name} className="w-[180px]" onBlur={field.handleBlur}>
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    {statuses.map((s) => (
                      <SelectItem key={s.value} value={s.value}>
                        {s.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FieldError meta={field.state.meta} show={form.state.submissionAttempts > 0} />
              </div>
            )}
          </form.Field>

          <form.Subscribe selector={(s) => [s.canSubmit, s.isSubmitting] as const}>
            {([canSubmit, isSubmitting]) => (
              <Button type="submit" disabled={!canSubmit || isSubmitting}>
                Submit
              </Button>
            )}
          </form.Subscribe>
        </form>
      </div>
    </main>
  );
};
