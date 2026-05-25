import type { AnyFieldMeta } from "@tanstack/react-form";

/**
 * Renders the first validation error for a TanStack Form field. Errors show
 * once the field has been touched, or whenever `show` is true (e.g. after a
 * submit attempt, so required-field errors surface for untouched fields).
 * With a Standard Schema validator (zod) the entries in `meta.errors` are
 * issue objects carrying a `message`; we fall back to stringifying anything
 * that isn't shaped that way.
 */
export function FieldError({ meta, show = false }: { meta: AnyFieldMeta; show?: boolean }) {
  if (!(meta.isTouched || show) || meta.errors.length === 0) return null;

  const first = meta.errors[0];
  const message =
    typeof first === "object" && first !== null && "message" in first
      ? String((first as { message: unknown }).message)
      : String(first);

  return <p className="text-sm text-destructive">{message}</p>;
}
