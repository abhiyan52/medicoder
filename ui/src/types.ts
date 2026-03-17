export type DocumentStatus = "uploaded" | "queued" | "processing" | "failed" | "processed";

export interface Condition {
  condition: string;
  code: string;
  hcc_relevant: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface AuthSession {
  username: string;
  token: string;
  tokenType: string;
}

export interface UploadDocumentRequest {
  title: string;
  file: File;
  token: string;
}

export interface UploadDocumentResponse {
  id: string;
  title: string;
  file_url: string;
  status: DocumentStatus;
  created_at: string;
  updated_at: string;
}

export interface DocumentHistoryItem {
  id: string;
  title: string;
  status: DocumentStatus;
  created_at: string;
  updated_at: string;
}

export interface DocumentHistoryPageResponse {
  items: DocumentHistoryItem[];
  next_page_token: string | null;
}

export interface ProcessedResultItem {
  id: string;
  extracted_code: {
    condition?: string | null;
    code?: string | null;
  } | null;
  hcc_code: {
    hcc_relevant?: boolean | null;
  } | null;
}

export interface DocumentDetail {
  id: string;
  title: string;
  file_url: string;
  status: DocumentStatus;
  extracted_text: string | null;
  processed_results: ProcessedResultItem[];
  created_at: string;
  updated_at: string;
  processed_at: string | null;
}
