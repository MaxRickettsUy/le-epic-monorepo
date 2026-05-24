// Server-side HTTP client for the backend API (see ../../backend/app).
// Base URL is read from API_URL so the host is never shipped to the browser.

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

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });

  if (!res.ok) {
    throw new ApiError(res.status, `${init.method ?? "GET"} ${path} failed (${res.status})`);
  }

  return res.json() as Promise<T>;
}

/** Like {@link apiFetch} but resolves to `null` on a 404 so callers can render not-found. */
export async function apiFetchOrNull<T>(path: string, init: RequestInit = {}): Promise<T | null> {
  try {
    return await apiFetch<T>(path, init);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}
