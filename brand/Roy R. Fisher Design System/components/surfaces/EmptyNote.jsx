import React from "react";

/* The empty state: a dashed box that says what is missing and what to do,
   never an illustration and never an error. */
export function EmptyNote({ name, state, action = null }) {
  return (
    <div className="rrf-emptynote">
      <div className="rrf-emptynote__name">{name}</div>
      {state ? <div className="rrf-emptynote__state">{state}</div> : null}
      {action ? <div style={{ marginTop: "var(--space-3)" }}>{action}</div> : null}
    </div>
  );
}
