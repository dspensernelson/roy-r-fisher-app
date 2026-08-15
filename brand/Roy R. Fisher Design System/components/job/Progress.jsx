import React from "react";

/* How far the report has got, in words and figures. Sits under the screen's
   actions, never as a bar on its own. */
export function Progress({ ready, total, noun = "sections" }) {
  return (
    <div className="rrf-progress">
      <b>{ready} of {total}</b> {noun} have everything they need
    </div>
  );
}
