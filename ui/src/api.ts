import type { ProcessResponse, HistoryEntry } from "./types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail ?? "Request failed");
  }
  return res.json();
}

export async function processNote(note: string): Promise<ProcessResponse> {
  const res = await fetch(`${BASE_URL}/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ note }),
  });
  return handleResponse<ProcessResponse>(res);
}

export async function processFile(file: File): Promise<ProcessResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE_URL}/process/file`, {
    method: "POST",
    body: form,
  });
  return handleResponse<ProcessResponse>(res);
}

export async function fetchHistory(): Promise<HistoryEntry[]> {
  const res = await fetch(`${BASE_URL}/history`);
  return handleResponse<HistoryEntry[]>(res);
}
