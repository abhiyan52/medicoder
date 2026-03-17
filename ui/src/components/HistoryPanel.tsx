import { useQuery } from "@tanstack/react-query";
import { fetchHistory } from "../api";
import type { HistoryEntry } from "../types";
import { HCCBadge } from "./HCCBadge";
import { ResultsTable } from "./ResultsTable";
import { useState } from "react";

export function HistoryPanel() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["history"],
    queryFn: fetchHistory,
  });

  const [expanded, setExpanded] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div style={{ padding: "24px", color: "#6b7280", textAlign: "center" }}>
        Loading history...
      </div>
    );
  }

  if (isError) {
    return (
      <div style={{ padding: "24px", textAlign: "center" }}>
        <p style={{ color: "#991b1b" }}>Failed to load history.</p>
        <button onClick={() => refetch()} style={linkBtn}>Retry</button>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div style={{ padding: "24px", color: "#6b7280", textAlign: "center" }}>
        No processed notes yet.
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
      {data.map((entry) => (
        <HistoryRow
          key={entry.note_id}
          entry={entry}
          isExpanded={expanded === entry.note_id}
          onToggle={() => setExpanded(expanded === entry.note_id ? null : entry.note_id)}
        />
      ))}
    </div>
  );
}

interface HistoryRowProps {
  entry: HistoryEntry;
  isExpanded: boolean;
  onToggle: () => void;
}

function HistoryRow({ entry, isExpanded, onToggle }: HistoryRowProps) {
  const date = entry.processed_at
    ? new Date(entry.processed_at).toLocaleString()
    : "Unknown date";

  return (
    <div
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: "8px",
        overflow: "hidden",
        background: "white",
      }}
    >
      <button
        onClick={onToggle}
        aria-expanded={isExpanded}
        style={{
          width: "100%",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "14px 16px",
          background: "none",
          border: "none",
          cursor: "pointer",
          textAlign: "left",
          gap: "12px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px", flex: 1, minWidth: 0 }}>
          <span style={{ fontWeight: 600, color: "#111827", fontFamily: "monospace" }}>
            {entry.note_id}
          </span>
          <span style={{ color: "#6b7280", fontSize: "13px", flexShrink: 0 }}>
            {entry.result_count} condition{entry.result_count !== 1 ? "s" : ""}
          </span>
          {entry.hcc_count > 0 && (
            <HCCBadge relevant={true} label={`${entry.hcc_count} HCC`} />
          )}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", flexShrink: 0 }}>
          <span style={{ color: "#9ca3af", fontSize: "12px" }}>{date}</span>
          <span style={{ color: "#6b7280", fontSize: "12px" }}>{isExpanded ? "▲" : "▼"}</span>
        </div>
      </button>

      {isExpanded && (
        <div style={{ padding: "0 16px 16px", borderTop: "1px solid #f3f4f6" }}>
          <ResultsTable results={entry.results} />
        </div>
      )}
    </div>
  );
}

const linkBtn: React.CSSProperties = {
  background: "none",
  border: "none",
  color: "#2563eb",
  cursor: "pointer",
  fontSize: "14px",
};
