import { ReactNode } from "react";

type Props = {
  icon?: ReactNode;
  /** t("…") */
  title: string;
  description?: string;
  /** زر الإجراء الأول — مهم في الحالة الفارغة الأولى */
  action?: ReactNode;
  variant?: "empty" | "error" | "filtered" | "forbidden";
};

const TONE = {
  empty:     "var(--text-faint)",
  filtered:  "var(--text-faint)",
  error:     "var(--danger)",
  forbidden: "var(--warning)",
};

export function EmptyState({ icon, title, description, action, variant = "empty" }: Props) {
  return (
    <div
      role={variant === "error" ? "alert" : undefined}
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 8,
        paddingBlock: 48,
        paddingInline: 24,
        textAlign: "center",
      }}
    >
      {icon && (
        <span
          aria-hidden="true"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            inlineSize: 56,
            blockSize: 56,
            borderRadius: "var(--radius-full)",
            background: "var(--surface-2)",
            color: TONE[variant],
            marginBlockEnd: 8,
          }}
        >
          {icon}
        </span>
      )}
      <p className="t-heading" style={{ color: "var(--text)", margin: 0 }}>{title}</p>
      {description && (
        <p className="t-body" style={{ color: "var(--text-muted)", margin: 0, maxInlineSize: 380 }}>
          {description}
        </p>
      )}
      {action && <div style={{ marginBlockStart: 12 }}>{action}</div>}
    </div>
  );
}
