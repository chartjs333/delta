import { Children, isValidElement, useEffect, useId, useRef, useState, type LabelHTMLAttributes, type ReactNode } from "react";
import { t, useLanguage } from "../i18n";
import { fieldHints } from "./field-help-content";
import "./field-help.css";

function labelText(children: ReactNode): string {
  return Children.toArray(children).map(child => {
    if (typeof child === "string" || typeof child === "number") return String(child);
    if (!isValidElement<{ children?: ReactNode }>(child)) return "";
    if (typeof child.type === "string" && ["input", "select", "textarea"].includes(child.type)) return "";
    return labelText(child.props.children);
  }).join("").trim();
}

export function FieldHelp({ field }: { field: string }) {
  const language = useLanguage();
  const [open, setOpen] = useState(false);
  const id = useId();
  const host = useRef<HTMLSpanElement>(null);
  const button = useRef<HTMLButtonElement>(null);
  const hint = fieldHints.find(item => item.labels.some(label => field === label || field === t(label)));
  useEffect(() => {
    if (!open) return;
    function close(event: PointerEvent) {
      if (!host.current?.contains(event.target as Node)) setOpen(false);
    }
    function escape(event: KeyboardEvent) {
      if (event.key === "Escape") { setOpen(false); button.current?.focus(); }
    }
    document.addEventListener("pointerdown", close);
    document.addEventListener("keydown", escape);
    return () => { document.removeEventListener("pointerdown", close); document.removeEventListener("keydown", escape); };
  }, [open]);
  if (!hint) return null;
  const [description, example] = hint[language];
  const name = `${language === "ru" ? "Подсказка" : "Help"}: ${t(field)}`;
  return <span className="field-help-anchor" ref={host}>
    <button ref={button} className="field-hint-button" type="button" aria-label={name} aria-expanded={open} aria-controls={id} onClick={() => setOpen(value => !value)}>ⓘ</button>
    {open ? <span id={id} className="field-hint-popover" role="note" aria-label={name}>
      <strong>{t(field)}</strong><span>{description}</span>
      <span className="field-hint-example"><b>{language === "ru" ? "Пример" : "Example"}</b><span>{example}</span></span>
    </span> : null}
  </span>;
}

// The help button is outside the label: opening guidance must never toggle a
// radio/checkbox or become part of the form control's accessible name.
export function HelpLabel({ children, className, ...props }: LabelHTMLAttributes<HTMLLabelElement>) {
  return <div className={`help-label ${className ?? ""}`}>
    <label {...props} className={className}>{children}</label>
    <FieldHelp field={labelText(children)} />
  </div>;
}
