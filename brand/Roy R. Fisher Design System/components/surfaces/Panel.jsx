import React from "react";

/* A paper card grouping fields or checkboxes under a small ruled label. Used
   for intake and the section picker: dense input, grouped by whether it is
   needed to start. */
export function Panel({ label, note, children }) {
  return (
    <div className="rrf-panel">
      {label ? <h2 className="rrf-panel__label">{label}</h2> : null}
      {children}
      {note ? <p className="rrf-panel__note">{note}</p> : null}
    </div>
  );
}
