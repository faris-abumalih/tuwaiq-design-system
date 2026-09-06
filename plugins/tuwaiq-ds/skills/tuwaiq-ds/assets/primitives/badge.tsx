type Variant = "brand" | "success" | "warning" | "danger" | "info" | "neutral";

type Props = {
  /** مرّر t("…") — لا نص مكتوب مباشرة */
  label: string;
  variant?: Variant;
  /** نقطة للحالات الحيّة (نشط / متوقف) */
  dot?: boolean;
};

const V: Record<Variant, { bg: string; fg: string }> = {
  brand:   { bg: "var(--brand-tint)",   fg: "var(--brand)" },
  success: { bg: "var(--success-tint)", fg: "var(--success)" },
  warning: { bg: "var(--warning-tint)", fg: "var(--warning)" },
  danger:  { bg: "var(--danger-tint)",  fg: "var(--danger)" },
  info:    { bg: "var(--info-tint)",    fg: "var(--info)" },
  neutral: { bg: "var(--surface-2)",    fg: "var(--text-muted)" },
};

export function Badge({ label, variant = "neutral", dot }: Props) {
  const v = V[variant];
  return (
    <span
      className="t-caption"
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        background: v.bg,
        color: v.fg,
        paddingInline: 8,
        paddingBlock: 4,
        borderRadius: "var(--radius-full)",
        fontWeight: "var(--fw-medium)",
        whiteSpace: "nowrap",
      }}
    >
      {dot && (
        <span
          aria-hidden="true"
          style={{ inlineSize: 6, blockSize: 6, borderRadius: "var(--radius-full)", background: v.fg, flexShrink: 0 }}
        />
      )}
      {label}
    </span>
  );
}
