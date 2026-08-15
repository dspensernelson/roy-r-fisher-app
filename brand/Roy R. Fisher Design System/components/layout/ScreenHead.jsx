import React from "react";

/* Title on the left, the things you can do on the right, one row, and nothing
   below it but the work itself. `stack` left-aligns the actions for form
   screens where the primary button belongs under the fields. */
export function ScreenHead({ title, sub, actions = null, below = null, stack = false }) {
  return (
    <div className={`rrf-screenhead${stack ? " rrf-screenhead--stack" : ""}`}>
      <div>
        <h1 className="rrf-title">{title}</h1>
        {sub ? <p className="rrf-sub">{sub}</p> : null}
      </div>
      {(actions || below) ? (
        <div className="rrf-screenhead__actions">
          {actions ? <div className="rrf-actionrow">{actions}</div> : null}
          {below}
        </div>
      ) : null}
    </div>
  );
}
