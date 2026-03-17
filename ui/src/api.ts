import type {
  AuthSession,
  DocumentDetail,
  DocumentHistoryPageResponse,
  LoginRequest,
  LoginResponse,
  UploadDocumentRequest,
  UploadDocumentResponse,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const SESSION_STORAGE_KEY = "medicoder-session";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new ApiError(payload.detail ?? "Request failed", response.status);
  }

  return response.json() as Promise<T>;
}

export async function login(payload: LoginRequest): Promise<AuthSession> {
  const body = new URLSearchParams();
  body.set("username", payload.username);
  body.set("password", payload.password);

  const response = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body,
  });

  const data = await handleResponse<LoginResponse>(response);
  const session = {
    username: payload.username,
    token: data.access_token,
    tokenType: data.token_type,
  };
  localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
  return session;
}

export function getSession(): AuthSession | null {
  const raw = localStorage.getItem(SESSION_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as AuthSession;
  } catch {
    localStorage.removeItem(SESSION_STORAGE_KEY);
    return null;
  }
}

export function clearSession() {
  localStorage.removeItem(SESSION_STORAGE_KEY);
}

function createAuthHeaders(token: string, extras?: Record<string, string>) {
  return {
    Authorization: `Bearer ${token}`,
    ...extras,
  };
}

export async function fetchDocuments(token: string): Promise<DocumentHistoryPageResponse> {
  const response = await fetch(`${BASE_URL}/documents`, {
    headers: createAuthHeaders(token),
  });

  return handleResponse<DocumentHistoryPageResponse>(response);
}

export async function fetchDocumentDetail(documentId: string, token: string): Promise<DocumentDetail> {
  const response = await fetch(`${BASE_URL}/documents/${documentId}`, {
    headers: createAuthHeaders(token),
  });

  return handleResponse<DocumentDetail>(response);
}

export async function uploadDocument({
  title,
  file,
  token,
}: UploadDocumentRequest): Promise<UploadDocumentResponse> {
  const formData = new FormData();
  formData.append("title", title);
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/documents`, {
    method: "POST",
    headers: createAuthHeaders(token),
    body: formData,
  });

  return handleResponse<UploadDocumentResponse>(response);
}
