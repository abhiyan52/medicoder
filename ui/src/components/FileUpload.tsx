import { useRef, useState } from "react";

interface FileUploadProps {
  onFile: (file: File) => void;
  isLoading: boolean;
}

export function FileUpload({ onFile, isLoading }: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [selected, setSelected] = useState<File | null>(null);

  function handleFile(file: File) {
    setSelected(file);
    onFile(file);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      <label style={{ fontWeight: 600 }}>Upload Clinical Note (.txt)</label>

      <div
        role="button"
        tabIndex={0}
        aria-label="Drop zone for clinical note file"
        onClick={() => !isLoading && inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && !isLoading && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${dragging ? "#2563eb" : "#d1d5db"}`,
          borderRadius: "8px",
          padding: "40px 24px",
          textAlign: "center",
          cursor: isLoading ? "not-allowed" : "pointer",
          background: dragging ? "#eff6ff" : "#f9fafb",
          transition: "border-color 0.15s, background 0.15s",
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".txt"
          style={{ display: "none" }}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />
        {selected ? (
          <div>
            <p style={{ margin: 0, fontWeight: 600, color: "#111827" }}>{selected.name}</p>
            <p style={{ margin: "4px 0 0", color: "#6b7280", fontSize: "13px" }}>
              {(selected.size / 1024).toFixed(1)} KB
            </p>
          </div>
        ) : (
          <div>
            <p style={{ margin: 0, color: "#374151" }}>
              Drop a <code>.txt</code> file here, or{" "}
              <span style={{ color: "#2563eb", fontWeight: 500 }}>browse</span>
            </p>
            <p style={{ margin: "4px 0 0", color: "#9ca3af", fontSize: "13px" }}>
              Plain text clinical notes only
            </p>
          </div>
        )}
      </div>

      {selected && !isLoading && (
        <button
          onClick={() => { setSelected(null); if (inputRef.current) inputRef.current.value = ""; }}
          style={{
            alignSelf: "flex-start",
            background: "none",
            border: "none",
            color: "#6b7280",
            cursor: "pointer",
            fontSize: "13px",
            padding: 0,
          }}
        >
          Clear selection
        </button>
      )}
    </div>
  );
}
