import { ReactNode } from "react";

type Props = {
  /** t("…") — عنوان واحد فقط في الصفحة */
  title: string;
  subtitle?: string;
  /** الإجراء الرئيسي — واحد فقط */
  action?: ReactNode;
};

export function PageHeader({ title, subtitle, action }: Props) {
  return (
    <header
      style={{
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "space-between",
        gap: 16,
        marginBlockEnd: 24,
        textAlign: "start",
      }}
    >
      <div>
        <h1 className="t-title" style={{ color: "var(--text)", margin: 0 }}>{title}</h1>
        {subtitle && (
          <p className="t-meta" style={{ color: "var(--text-muted)", marginBlockStart: 4, margin: 0 }}>
            {subtitle}
          </p>
        )}
      </div>
      {action && <div style={{ flexShrink: 0 }}>{action}</div>}
    </header>
  );
}
