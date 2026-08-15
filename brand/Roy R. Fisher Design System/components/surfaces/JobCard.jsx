import React from "react";

/* One job folder. White paper with the firm's red rule on top. The card
   answers "which job needs me" on its own: the one thing to do next, and how
   far the report has got. `next.tone` is "do" (he can act now), "waiting"
   (something is missing that he cannot produce) or "done" (nothing pending). */
export function JobCard({ city, address, meta, next, ready, total, onClick }) {
  const tone = (next && next.tone) || "do";
  const icon = tone === "done" ? "check" : tone === "waiting" ? "triangle-alert" : "chevron-right";
  const pct = total ? Math.round((ready / total) * 100) : 0;
  return (
    <button className="rrf-jobcard" onClick={onClick}>
      <div className="rrf-jobcard__city">{city || "Job"}</div>
      <div className="rrf-jobcard__addr">{address}</div>
      {meta ? <div className="rrf-jobcard__meta">{meta}</div> : null}
      {next ? (
        <div className={`rrf-jobcard__next${tone === "do" ? "" : ` rrf-jobcard__next--${tone}`}`}>
          <svg className="rrf-icon" aria-hidden="true"><use href={`${next.sprite || "assets/icons/sprite.svg"}#${icon}`} /></svg>
          <span>{next.label}</span>
        </div>
      ) : null}
      {total ? (
        <div className="rrf-jobcard__far">
          <span>{ready} of {total}</span>
          <span className={`rrf-jobcard__bar${ready === total ? " rrf-jobcard__bar--done" : ""}`}>
            <span style={{ width: `${pct}%` }} />
          </span>
        </div>
      ) : null}
    </button>
  );
}
