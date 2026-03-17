interface HCCBadgeProps {
  relevant: boolean;
  label?: string;
}

export function HCCBadge({ relevant, label }: HCCBadgeProps) {
  return (
    <span className={relevant ? "hcc-badge hcc-badge-positive" : "hcc-badge"}>
      {label ?? (relevant ? "Relevant" : "Not relevant")}
    </span>
  );
}
