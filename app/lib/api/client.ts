// Server-side HTTP client for the backend API (see ../../backend/app).
// Base URL is read from API_URL so the host is never shipped to the browser.
// Every response is validated against a zod schema at this boundary; a mismatch
// throws ApiParseError, which bubbles to the nearest error.tsx boundary.

import type { ZodType } from "zod";

const API_BASE = process.env.API_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Thrown when a 2xx response does not match the expected schema (contract drift). */
export class ApiParseError extends Error {
  constructor(
    public path: string,
    public issues: string,
  ) {
    super(`Response from ${path} did not match the expected schema: ${issues}`);
    this.name = "ApiParseError";
  }
}

export async function apiFetch<T>(
  path: string,
  schema: ZodType<T>,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });

  if (!res.ok) {
    throw new ApiError(res.status, `${init.method ?? "GET"} ${path} failed (${res.status})`);
  }

  let json: unknown;
  try {
    json = await res.json();
  } catch (err) {
    throw new ApiParseError(path, err instanceof Error ? err.message : String(err));
  }
  const result = schema.safeParse(json);
  if (!result.success) {
    throw new ApiParseError(path, result.error.message);
  }
  return result.data;
}

/** Like {@link apiFetch} but resolves to `null` on a 404 so callers can render not-found. */
export async function apiFetchOrNull<T>(
  path: string,
  schema: ZodType<T>,
  init: RequestInit = {},
): Promise<T | null> {
  try {
    return await apiFetch<T>(path, schema, init);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}
