interface HCCBadgeProps {
  relevant: boolean;
  label?: string;
}

export function HCCBadge({ relevant, label }: HCCBadgeProps) {
  const text = label ?? (relevant ? "HCC" : "—");
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 10px",
        borderRadius: "12px",
        fontSize: "12px",
        fontWeight: 600,
        background: relevant ? "#dcfce7" : "#f3f4f6",
        color: relevant ? "#166534" : "#6b7280",
        border: `1px solid ${relevant ? "#bbf7d0" : "#e5e7eb"}`,
        whiteSpace: "nowrap",
      }}
    >
      {text}
    </span>
  );
}
