import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { processNote, processFile } from "./api";
import { NoteInput } from "./components/NoteInput";
import { FileUpload } from "./components/FileUpload";
import { ResultsTable } from "./components/ResultsTable";
import { ErrorMessage } from "./components/ErrorMessage";
import { HistoryPanel } from "./components/HistoryPanel";

type InputTab = "paste" | "upload";
type ViewTab = "process" | "history";

export default function App() {
  const [viewTab, setViewTab] = useState<ViewTab>("process");
  const [inputTab, setInputTab] = useState<InputTab>("paste");
  const [note, setNote] = useState("");
  const queryClient = useQueryClient();

  const { mutate, data, isPending, isError, error, reset } = useMutation({
    mutationFn: (payload: { type: "text"; note: string } | { type: "file"; file: File }) =>
      payload.type === "text" ? processNote(payload.note) : processFile(payload.file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["history"] });
    },
  });

  function handlePasteSubmit() {
    const normalized = note.trim();
    if (!normalized) return;

    mutate({ type: "text", note: normalized });
    reset();
  }

  function handleFileSelected(file: File) {
    reset();
    mutate({ type: "file", file });
  }

  return (
    <div style={{ minHeight: "100vh", background: "#f8fafc", display: "flex", flexDirection: "column", alignItems: "center", padding: "40px 16px" }}>
      <div style={{ width: "100%", maxWidth: "860px", display: "flex", flexDirection: "column", gap: "24px" }}>

        {/* Header */}
        <header>
          <h1 style={{ margin: 0, fontSize: "28px", fontWeight: 700, color: "#111827" }}>Medicoder</h1>
          <p style={{ margin: "4px 0 0", color: "#6b7280", fontSize: "15px" }}>
            Extract ICD-10 conditions and HCC relevance from clinical notes
          </p>
        </header>

        {/* Top-level tabs */}
        <div style={{ display: "flex", borderBottom: "1px solid #e5e7eb", gap: "0" }}>
          {(["process", "history"] as ViewTab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setViewTab(tab)}
              style={{
                padding: "10px 20px",
                background: "none",
                border: "none",
                borderBottom: viewTab === tab ? "2px solid #2563eb" : "2px solid transparent",
                color: viewTab === tab ? "#2563eb" : "#6b7280",
                fontWeight: viewTab === tab ? 600 : 400,
                fontSize: "14px",
                cursor: "pointer",
                textTransform: "capitalize",
              }}
            >
              {tab === "process" ? "Process Note" : "History"}
            </button>
          ))}
        </div>

        {/* Process view */}
        {viewTab === "process" && (
          <>
            <section style={card}>
              {/* Input method tabs */}
              <div style={{ display: "flex", gap: "8px", marginBottom: "20px" }}>
                {(["paste", "upload"] as InputTab[]).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => { setInputTab(tab); reset(); }}
                    style={{
                      padding: "6px 16px",
                      borderRadius: "6px",
                      border: "1px solid",
                      borderColor: inputTab === tab ? "#2563eb" : "#e5e7eb",
                      background: inputTab === tab ? "#eff6ff" : "white",
                      color: inputTab === tab ? "#2563eb" : "#374151",
                      fontWeight: inputTab === tab ? 600 : 400,
                      fontSize: "13px",
                      cursor: "pointer",
                    }}
                  >
                    {tab === "paste" ? "Paste Text" : "Upload File"}
                  </button>
                ))}
              </div>

              {inputTab === "paste" ? (
                <NoteInput
                  value={note}
                  onChange={setNote}
                  onSubmit={handlePasteSubmit}
                  isLoading={isPending}
                />
              ) : (
                <FileUpload onFile={handleFileSelected} isLoading={isPending} />
              )}
            </section>

            {isPending && (
              <div style={{ textAlign: "center", color: "#6b7280", fontSize: "14px" }}>
                Running pipeline...
              </div>
            )}

            {isError && <ErrorMessage message={(error as Error).message} />}

            {data && data.results.length === 0 && (
              <p style={{ textAlign: "center", color: "#6b7280" }}>No conditions found in this note.</p>
            )}

            {data && data.results.length > 0 && (
              <section style={card}>
                <div style={{ marginBottom: "12px", fontSize: "13px", color: "#6b7280" }}>
                  Saved as <code style={{ color: "#111827" }}>{data.note_id}</code>
                </div>
                <ResultsTable results={data.results} />
              </section>
            )}
          </>
        )}

        {/* History view */}
        {viewTab === "history" && (
          <section style={card}>
            <h2 style={{ margin: "0 0 16px", fontSize: "18px" }}>Processed Notes</h2>
            <HistoryPanel />
          </section>
        )}
      </div>
    </div>
  );
}

const card: React.CSSProperties = {
  background: "white",
  borderRadius: "12px",
  border: "1px solid #e5e7eb",
  padding: "24px",
};
