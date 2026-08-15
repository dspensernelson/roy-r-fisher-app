import React from "react";

/* The job screen's two columns. Not an even split: the left rows carry a
   folder's whole missing list and wrap badly when squeezed. */
export function Bands({ left, right }) {
  return (
    <div className="rrf-bands">
      <div>{left}</div>
      <div>{right}</div>
    </div>
  );
}
