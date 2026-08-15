import React from "react";

/* A button that reads as a link: Cancel, Add photos, Change sections. Used
   wherever an action must be available but must not compete. */
export function LinkButton({ onClick, disabled = false, size = "fine", children }) {
  return (
    <button type="button" onClick={onClick} disabled={disabled}
      className={`rrf-link${size === "body" ? " rrf-link--body" : ""}`}>
      {children}
    </button>
  );
}
