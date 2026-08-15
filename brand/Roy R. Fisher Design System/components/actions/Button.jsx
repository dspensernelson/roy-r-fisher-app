import React from "react";

/* One primary button per screen, in brand red. `secondary` is the blue used
   for the second-most-likely action; `quiet` is a white outlined button for
   anything reversible. Disabled is a real state, not a hidden button. */
export function Button({ variant = "primary", size = "md", disabled = false, onClick, type = "button", children }) {
  return (
    <button type={type} disabled={disabled} onClick={onClick}
      className={`rrf-btn rrf-btn--${variant}${size === "sm" ? " rrf-btn--sm" : ""}`}>
      {children}
    </button>
  );
}
