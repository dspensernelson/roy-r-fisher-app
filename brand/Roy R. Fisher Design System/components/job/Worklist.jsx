import React from "react";

/* A titled group of task rows. The proposal uses two groups — "You can do
   these now" and "Already here" — and deliberately has no "waiting on someone
   else" group, because nothing in the app knows who was asked. That is a
   product call, not a constraint of this component: pass any title. */
export function Worklist({ title, children }) {
  return (
    <>
      {title ? <p className="rrf-subhead">{title}</p> : null}
      <div className="rrf-worklist">{children}</div>
    </>
  );
}
