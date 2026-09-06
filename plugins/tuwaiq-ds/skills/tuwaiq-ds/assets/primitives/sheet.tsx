import { ReactNode, useEffect } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import { TuwayqButton } from "./tuwayq-button";

type Base = {
  open: boolean;
  onClose: () => void;
  /** t("…") */
  title: string;
  description?: string;
  children?: ReactNode;
  /** أزرار التذييل — الرئيسي أولًا */
  footer?: ReactNode;
  /** t("…") لزر الإغلاق الأيقوني */
  closeLabel: string;
};

function useEscape(open: boolean, onClose: () => void) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onClose]);
}

function Scrim({ onClose, children }: { onClose: () => void; children: ReactNode }) {
  return createPortal(
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 100,
        background: "rgba(17, 19, 24, 0.32)", // ds-allow: no-raw-color — طبقة تعتيم، ليست لونًا دلاليًا
        display: "flex",
        animation: "twq-fade var(--dur-base) var(--ease)",
      }}
    >
      {children}
    </div>,
    document.body,
  );
}

function Header({ title, description, onClose, closeLabel }:
  { title: string; description?: string; onClose: () => void; closeLabel: string }) {
  return (
    <div style={{ display: "flex", alignItems: "flex-start", gap: 16, padding: 24, paddingBlockEnd: 16 }}>
      <div style={{ flex: 1, textAlign: "start" }}>
        <h2 className="t-heading" style={{ color: "var(--text)", margin: 0 }}>{title}</h2>
        {description && (
          <p className="t-body" style={{ color: "var(--text-muted)", margin: 0, marginBlockStart: 6 }}>
            {description}
          </p>
        )}
      </div>
      <button
        type="button"
        onClick={onClose}
        aria-label={closeLabel}
        style={{
          display: "flex", alignItems: "center", justifyContent: "center",
          inlineSize: 32, blockSize: 32, flexShrink: 0,
          borderRadius: "var(--radius-full)", border: "none",
          background: "var(--surface-2)", color: "var(--text-muted)", cursor: "pointer",
        }}
      >
        <X size={16} aria-hidden="true" />
      </button>
    </div>
  );
}

/** مودال — للقرارات التي تحتاج تركيزًا */
export function Modal({ open, onClose, title, description, children, footer, closeLabel }: Base) {
  useEscape(open, onClose);
  if (!open) return null;
  return (
    <Scrim onClose={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
        style={{
          margin: "auto",
          inlineSize: "min(560px, calc(100% - 48px))",
          maxBlockSize: "calc(100% - 64px)",
          overflowY: "auto",
          background: "var(--surface)",
          borderRadius: "var(--radius-xl)",
          boxShadow: "var(--shadow-3)",
          animation: "twq-rise var(--dur-slow) var(--ease)",
        }}
      >
        <Header title={title} description={description} onClose={onClose} closeLabel={closeLabel} />
        <div style={{ paddingInline: 24 }}>{children}</div>
        {footer && (
          <div style={{ display: "flex", gap: 8, padding: 24, paddingBlockStart: 20 }}>{footer}</div>
        )}
      </div>
    </Scrim>
  );
}

/** سايد شيت — للتفاصيل والإعدادات؛ يفتح من جهة البداية في RTL */
export function SideSheet({ open, onClose, title, description, children, footer, closeLabel }: Base) {
  useEscape(open, onClose);
  if (!open) return null;
  return (
    <Scrim onClose={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
        style={{
          marginInlineStart: "auto",
          inlineSize: "min(480px, 100%)",
          blockSize: "100%",
          display: "flex",
          flexDirection: "column",
          background: "var(--surface)",
          borderStartStartRadius: "var(--radius-2xl)",
          borderEndStartRadius: "var(--radius-2xl)",
          boxShadow: "var(--shadow-3)",
          animation: "twq-slide-in var(--dur-slow) var(--ease)",
        }}
      >
        <Header title={title} description={description} onClose={onClose} closeLabel={closeLabel} />
        <div style={{ flex: 1, overflowY: "auto", paddingInline: 24 }}>{children}</div>
        {footer && (
          <div style={{ display: "flex", gap: 8, padding: 24, borderBlockStart: "1px solid var(--hairline)" }}>
            {footer}
          </div>
        )}
      </div>
    </Scrim>
  );
}

/** تأكيد — إلزامي لكل إجراء لا رجعة فيه */
export function ConfirmDialog({
  open, onClose, onConfirm, title, description, confirmLabel, cancelLabel, closeLabel, tone = "danger",
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  /** t("…", { name }) — يذكر اسم الشيء بالضبط */
  title: string;
  description?: string;
  confirmLabel: string;
  cancelLabel: string;
  closeLabel: string;
  tone?: "danger" | "primary";
}) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      description={description}
      closeLabel={closeLabel}
      footer={
        <>
          <TuwayqButton variant={tone === "danger" ? "danger" : "primary"} onClick={onConfirm}>
            {confirmLabel}
          </TuwayqButton>
          <TuwayqButton variant="ghost" onClick={onClose}>{cancelLabel}</TuwayqButton>
        </>
      }
    />
  );
}
