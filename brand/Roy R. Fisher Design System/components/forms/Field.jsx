import React from "react";

/* One labelled input: paper, hairline, 6px — the same object as a row. There
   is one tone; the app has no dark fields. `derived` marks a value that fills
   itself in until edited. `error` and `hint` are part of the field, not a
   separate line below it. */
export function Field({
  label, value, onChange, placeholder, type = "text",
  options = null, hint, error, mono = false, derived = false, disabled = false,
  autoFocus = false, onKeyDown, name,
}) {
  const cls = ["rrf-field", derived ? "is-derived" : "", mono ? "is-mono" : "", error ? "is-error" : ""]
    .filter(Boolean).join(" ");
  return (
    <label className={cls}>
      {label ? <span className="rrf-field__label">{label}</span> : null}
      {options ? (
        <select className="rrf-field__input" value={value} disabled={disabled} name={name}
          onChange={(e) => onChange && onChange(e.target.value)}>
          <option value="">Choose one</option>
          {options.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
      ) : (
        <input className="rrf-field__input" type={type} value={value} placeholder={placeholder}
          disabled={disabled} autoFocus={autoFocus} name={name} onKeyDown={onKeyDown}
          spellCheck="false" autoComplete="off"
          onChange={(e) => onChange && onChange(e.target.value)} />
      )}
      {(error || hint) ? <span className="rrf-field__hint">{error || hint}</span> : null}
    </label>
  );
}
