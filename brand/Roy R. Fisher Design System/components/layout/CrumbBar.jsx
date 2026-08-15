import React from "react";

/* The charcoal bar under the masthead: where you are, and Settings on the far
   right. Crumbs are buttons because the app has no URLs. */
export function CrumbBar({ trail = [], right = null }) {
  return (
    <div className="rrf-crumbbar">
      <nav className="rrf-crumbbar__inner">
        {trail.map((c, i) => (
          <React.Fragment key={c.label}>
            {i > 0 ? <span className="rrf-crumb-sep">{"\u203A"}</span> : null}
            {c.onClick ? (
              <button className="rrf-crumb" onClick={c.onClick}>{c.label}</button>
            ) : (
              <span className="rrf-crumb rrf-crumb--tail">{c.label}</span>
            )}
          </React.Fragment>
        ))}
        {right ? <div className="rrf-crumbbar__right">{right}</div> : null}
      </nav>
    </div>
  );
}
