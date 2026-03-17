import type { Condition } from "../types";
import { HCCBadge } from "./HCCBadge";

interface ResultsTableProps {
  results: Condition[];
}

export function ResultsTable({ results }: ResultsTableProps) {
  const hccCount = results.filter((r) => r.hcc_relevant).length;

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "12px",
        }}
      >
        <h2 style={{ margin: 0, fontSize: "18px" }}>
          Results{" "}
          <span style={{ color: "#6b7280", fontWeight: 400 }}>
            ({results.length} condition{results.length !== 1 ? "s" : ""})
          </span>
        </h2>
        <span style={{ fontSize: "13px", color: "#2563eb", fontWeight: 500 }}>
          {hccCount} HCC-relevant
        </span>
      </div>

      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: "14px",
          }}
        >
          <thead>
            <tr style={{ background: "#f9fafb" }}>
              <th scope="col" style={th}>#</th>
              <th scope="col" style={{ ...th, textAlign: "left" }}>Condition</th>
              <th scope="col" style={th}>ICD-10 Code</th>
              <th scope="col" style={th}>HCC</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r, i) => (
              <tr
                key={i}
                style={{
                  borderTop: "1px solid #e5e7eb",
                  background: r.hcc_relevant ? "#f0fdf4" : "white",
                }}
              >
                <td style={{ ...td, color: "#9ca3af", width: "40px" }}>{i + 1}</td>
                <td style={{ ...td, fontWeight: 500 }}>{r.condition}</td>
                <td style={{ ...td, textAlign: "center", fontFamily: "monospace" }}>
                  {r.code}
                </td>
                <td style={{ ...td, textAlign: "center" }}>
                  <HCCBadge relevant={r.hcc_relevant} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const th: React.CSSProperties = {
  padding: "10px 12px",
  textAlign: "center",
  fontWeight: 600,
  fontSize: "12px",
  textTransform: "uppercase",
  color: "#6b7280",
  letterSpacing: "0.05em",
};

const td: React.CSSProperties = {
  padding: "12px",
};
