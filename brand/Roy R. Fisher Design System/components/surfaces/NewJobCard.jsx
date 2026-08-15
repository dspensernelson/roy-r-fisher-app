import React from "react";

/* The empty slot at the end of the job grid. Dashed, in link blue: nothing
   exists here yet. */
export function NewJobCard({ onClick, label = "+ New job" }) {
  return <button className="rrf-jobcard rrf-jobcard--new" onClick={onClick}>{label}</button>;
}
