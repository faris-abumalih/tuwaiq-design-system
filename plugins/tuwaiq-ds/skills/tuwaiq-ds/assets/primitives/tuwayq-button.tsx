import { ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";

type Props = {
  children: ReactNode;
  variant?: Variant;
  /** توضع بعد النص في الـ JSX — تظهر يمينه في RTL */
  icon?: ReactNode;
  onClick?: () => void;
  type?: "button" | "submit" | "reset";
  disabled?: boolean;
  loading?: boolean;
  /** للأزرار الأيقونية فقط — مرّر t("…") */
  ariaLabel?: string;
  fullWidth?: boolean;
};

const V: Record<Variant, { bg: string; fg: string }> = {
  primary:   { bg: "var(--brand)",      fg: "var(--brand-fg)" },
  secondary: { bg: "var(--brand-tint)", fg: "var(--brand)" },
  ghost:     { bg: "transparent",       fg: "var(--text)" },
  danger:    { bg: "var(--danger-tint)", fg: "var(--danger)" },
};

export function TuwayqButton({
  children, variant = "primary", icon, onClick, type = "button",
  disabled = false, loading = false, ariaLabel, fullWidth = false,
}: Props) {
  const v = V[variant];
  const off = disabled || loading;
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={off}
      aria-label={ariaLabel}
      aria-busy={loading}
      className="t-body-lg"
      style={{
        display: fullWidth ? "flex" : "inline-flex",
        width: fullWidth ? "100%" : undefined,
        alignItems: "center",
        justifyContent: "center",
        gap: 6,
        background: v.bg,
        color: v.fg,
        paddingInline: 20,
        blockSize: "var(--control-height)",
        minInlineSize: "var(--touch-min)",
        borderRadius: "var(--radius-full)",
        border: "none",
        fontFamily: "var(--font-family)",
        cursor: off ? "not-allowed" : "pointer",
        opacity: off ? 0.5 : 1,
        transition: "background var(--dur-fast) var(--ease), opacity var(--dur-fast) var(--ease)",
        whiteSpace: "nowrap",
        flexShrink: 0,
      }}
    >
      {children}
      {loading ? <Spinner /> : icon}
    </button>
  );
}

function Spinner() {
  return (
    <span
      aria-hidden="true"
      style={{
        inlineSize: 14,
        blockSize: 14,
        borderRadius: "var(--radius-full)",
        border: "2px solid currentColor",
        borderBlockStartColor: "transparent",
        animation: "twq-spin 700ms linear infinite",
      }}
    />
  );
}
