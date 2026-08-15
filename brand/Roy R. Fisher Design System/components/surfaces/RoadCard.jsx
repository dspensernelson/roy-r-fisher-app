import React from "react";

/* Two ways into the same form. A road is a choice of route, not a setting, so
   it is a card you press. `soon` marks a road that is not built yet — shown,
   because hiding it makes the app look smaller than the plan. */
export function RoadCard({ title, body, soon = false, onClick }) {
  return (
    <button className="rrf-roadcard" onClick={onClick} disabled={soon && !onClick}>
      <span className="rrf-roadcard__title">{title}</span>
      <span className="rrf-roadcard__body">{body}</span>
      {soon ? <span className="rrf-tag-soon">Not built yet</span> : null}
    </button>
  );
}
