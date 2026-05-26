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
import { Header } from "@/components/ui/header";
import { FieldError } from "@/components/forms/field-error";
import { releaseTypes } from "@/lib/const";
import { releaseFormSchema, type ReleaseFormValues } from "@/lib/schemas";

const START_YEAR = 1982;
const END_YEAR = new Date().getFullYear();

export const ReleaseForm = ({
  title,
  defaultValues,
  onSubmit,
}: {
  title: string;
  defaultValues?: Partial<ReleaseFormValues>;
  onSubmit: (input: ReleaseFormValues) => Promise<void>;
}) => {
  const initialValues: ReleaseFormValues = {
    name: defaultValues?.name ?? "",
    label: defaultValues?.label ?? null,
    release_type: defaultValues?.release_type ?? null,
    year: defaultValues?.year ?? null,
    length: defaultValues?.length ?? null,
    art: defaultValues?.art ?? null,
  };

  const form = useForm({
    defaultValues: initialValues,
    validators: { onChange: releaseFormSchema },
    onSubmit: async ({ value }) => {
      await onSubmit(value);
    },
  });

  return (
    <main className="flex-col pb-[1rem]">
      <Header />
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

          <form.Field name="year">
            {(field) => (
              <div className="flex flex-col gap-[0.5rem]">
                <Label htmlFor={field.name}>Year</Label>
                <Select
                  value={field.state.value ? String(field.state.value) : undefined}
                  onValueChange={(y) => field.handleChange(Number(y))}
                >
                  <SelectTrigger id={field.name} className="w-[180px]" onBlur={field.handleBlur}>
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
                <FieldError meta={field.state.meta} show={form.state.submissionAttempts > 0} />
              </div>
            )}
          </form.Field>

          <form.Field name="release_type">
            {(field) => (
              <div className="flex flex-col gap-[0.5rem]">
                <Label htmlFor={field.name}>Release Type</Label>
                <Select value={field.state.value ?? undefined} onValueChange={field.handleChange}>
                  <SelectTrigger id={field.name} className="w-[180px]" onBlur={field.handleBlur}>
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
                  value={field.state.value ?? ""}
                  onBlur={field.handleBlur}
                  onChange={(e) => field.handleChange(e.target.value || null)}
                  type="text"
                  placeholder="Label"
                />
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
