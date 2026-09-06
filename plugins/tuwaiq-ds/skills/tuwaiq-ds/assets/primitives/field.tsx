import { ReactNode, useId } from "react";
import { AlertCircle } from "lucide-react";

type Props = {
  /** t("…") — اللابل فوق الحقل دائمًا، مو placeholder بديل عنه */
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  /** تلميح قصير تحت الحقل */
  hint?: string;
  /** نص الخطأ — t("…") */
  error?: string;
  required?: boolean;
  disabled?: boolean;
  multiline?: boolean;
  /** "ltr" للروابط والبريد والأرقام اللاتينية */
  dir?: "rtl" | "ltr" | "auto";
  type?: "text" | "email" | "url" | "tel" | "number";
  trailing?: ReactNode;
};

export function Field({
  label, value, onChange, placeholder, hint, error,
  required, disabled, multiline, dir, type = "text", trailing,
}: Props) {
  const id = useId();
  const invalid = Boolean(error);
  const shared = {
    id,
    value,
    placeholder,
    disabled,
    dir,
    "aria-invalid": invalid,
    "aria-describedby": error ? `${id}-err` : hint ? `${id}-hint` : undefined,
    onChange: (e: { target: { value: string } }) => onChange(e.target.value),
    className: "t-body",
    style: {
      inlineSize: "100%",
      background: disabled ? "var(--surface-3)" : "var(--surface-2)",
      color: disabled ? "var(--text-disabled)" : "var(--text)",
      fontFamily: "var(--font-family)",
      border: invalid ? "1px solid var(--danger)" : "1px solid transparent",
      borderRadius: "var(--radius-md)",
      paddingInline: 12,
      paddingBlock: multiline ? 12 : 0,
      blockSize: multiline ? undefined : "var(--field-height)",
      minBlockSize: multiline ? 96 : undefined,
      resize: multiline ? ("vertical" as const) : undefined,
      outline: "none",
      transition: "border-color var(--dur-fast) var(--ease)",
    },
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6, textAlign: "start" }}>
      <label htmlFor={id} className="t-label" style={{ color: "var(--text)" }}>
        {label}
        {required && <span aria-hidden="true" style={{ color: "var(--danger)", marginInlineStart: 4 }}>*</span>}
      </label>

      <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
        {multiline ? <textarea {...shared} /> : <input {...shared} type={type} />}
        {trailing && (
          <span style={{ position: "absolute", insetInlineEnd: 12, display: "flex", color: "var(--text-faint)" }}>
            {trailing}
          </span>
        )}
      </div>

      {error ? (
        <span id={`${id}-err`} className="t-caption"
              style={{ display: "flex", alignItems: "center", gap: 4, color: "var(--danger)" }}>
          <AlertCircle size={14} aria-hidden="true" />
          {error}
        </span>
      ) : hint ? (
        <span id={`${id}-hint`} className="t-caption" style={{ color: "var(--text-muted)" }}>{hint}</span>
      ) : null}
    </div>
  );
}
