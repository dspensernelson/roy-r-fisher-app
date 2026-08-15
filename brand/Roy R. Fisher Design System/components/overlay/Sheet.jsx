import React from "react";

/* A step, not a parked option: asked when the user clicks the thing it
   affects. Escape closes it, clicking the scrim closes it, and the footer
   stays put so the button they came for is never below the fold. */
export function Sheet({ title, sub, children, foot, onClose, label }) {
  React.useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape" && onClose) onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="rrf-sheet-back" onClick={(e) => { if (e.target === e.currentTarget && onClose) onClose(); }}>
      <div className="rrf-sheet" role="dialog" aria-modal="true" aria-label={label || title}>
        {title ? <h2 className="rrf-sheet__title">{title}</h2> : null}
        {sub ? <p className="rrf-sheet__sub">{sub}</p> : null}
        {children}
        {foot ? <div className="rrf-sheet__foot">{foot}</div> : null}
      </div>
    </div>
  );
}
