export interface Condition {
  condition: string;
  code: string;
  hcc_relevant: boolean;
}

export interface ProcessResponse {
  note_id: string;
  results: Condition[];
}

export interface HistoryEntry {
  note_id: string;
  result_count: number;
  hcc_count: number;
  processed_at: string;
  results: Condition[];
}
