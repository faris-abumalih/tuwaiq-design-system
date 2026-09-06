import { ReactNode } from "react";
import { TrendingUp, TrendingDown } from "lucide-react";

type Props = {
  /** t("…") */
  label: string;
  value: string | number;
  icon?: ReactNode;
  /** نسبة التغيّر عن الفترة السابقة، موجبة أو سالبة */
  trend?: number;
  /** t("…") — نص المقارنة، مثل «عن الفترة السابقة» */
  trendLabel?: string;
  hint?: string;
};

export function StatCard({ label, value, icon, trend, trendLabel, hint }: Props) {
  const up = (trend ?? 0) >= 0;
  const tone = up ? "var(--success)" : "var(--danger)";
  const TrendIcon = up ? TrendingUp : TrendingDown;
  return (
    <div
      style={{
        background: "var(--surface)",
        borderRadius: "var(--radius-lg)",
        padding: 20,
        blockSize: "100%",
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "space-between",
        gap: 16,
        textAlign: "start",
      }}
    >
      <div>
        <p className="t-meta" style={{ color: "var(--text-muted)", margin: 0 }}>{label}</p>
        <p className="t-title" style={{ color: "var(--text)", margin: 0, marginBlockStart: 6 }}>{value}</p>

        {trend !== undefined && (
          <div style={{ display: "flex", alignItems: "center", gap: 4, marginBlockStart: 6 }}>
            <TrendIcon size={14} style={{ color: tone }} aria-hidden="true" />
            <span className="t-caption" style={{ color: tone, fontWeight: "var(--fw-semibold)" }} dir="ltr">
              {Math.abs(trend)}%
            </span>
            {trendLabel && <span className="t-caption" style={{ color: "var(--text-faint)" }}>{trendLabel}</span>}
          </div>
        )}
        {hint && <p className="t-caption" style={{ color: "var(--text-faint)", marginBlockStart: 6 }}>{hint}</p>}
      </div>

      {icon && (
        <span
          aria-hidden="true"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            inlineSize: 40,
            blockSize: 40,
            borderRadius: "var(--radius-md)",
            background: "var(--brand-tint)",
            color: "var(--brand)",
            flexShrink: 0,
          }}
        >
          {icon}
        </span>
      )}
    </div>
  );
}
