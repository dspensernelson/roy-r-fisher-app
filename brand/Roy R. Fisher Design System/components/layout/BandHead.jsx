import React from "react";

/* The small ruled heading over a band of rows. The note says where the
   rows came from; the action is a quiet link, never a button. */
export function BandHead({ title, note, action = null }) {
  return (
    <div className="rrf-bandhead">
      <h2 className="rrf-bandhead__title">{title}</h2>
      {note ? <span className="rrf-bandhead__note">{note}</span> : null}
      {action}
    </div>
  );
}
