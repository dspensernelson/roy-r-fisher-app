import React from "react";

/* Something has to move while the machine is working: writing a dozen
   captions takes real seconds, and a screen that sits still reads as broken.
   Determinate progress is never faked — this bar sweeps. */
export function Working({ label }) {
  return (
    <div className="rrf-working">
      <div className="rrf-sweep"><span /></div>
      {label ? <span className="rrf-working__text">{label}</span> : null}
    </div>
  );
}
