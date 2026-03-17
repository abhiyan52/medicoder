interface NoteInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

export function NoteInput({ value, onChange, onSubmit, isLoading }: NoteInputProps) {
  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      onSubmit();
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      <label htmlFor="clinical-note" style={{ fontWeight: 600 }}>
        Clinical Note
      </label>
      <textarea
        id="clinical-note"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Paste the clinical progress note here..."
        rows={12}
        disabled={isLoading}
        style={{
          width: "100%",
          padding: "12px",
          fontFamily: "monospace",
          fontSize: "14px",
          border: "1px solid #d1d5db",
          borderRadius: "8px",
          resize: "vertical",
          boxSizing: "border-box",
        }}
      />
      <button
        onClick={onSubmit}
        disabled={isLoading || !value.trim()}
        style={{
          alignSelf: "flex-end",
          padding: "10px 24px",
          background: isLoading || !value.trim() ? "#9ca3af" : "#2563eb",
          color: "white",
          border: "none",
          borderRadius: "8px",
          cursor: isLoading || !value.trim() ? "not-allowed" : "pointer",
          fontWeight: 600,
          fontSize: "14px",
        }}
      >
        {isLoading ? "Processing..." : "Extract Conditions"}
      </button>
      <p style={{ fontSize: "12px", color: "#6b7280", margin: 0 }}>
        Tip: Cmd+Enter to submit
      </p>
    </div>
  );
}
