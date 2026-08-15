import React from "react";
import { Chip } from "../actions/Chip.jsx";

/* One section of the report, in print order. Live rows carry a red left rule
   and a chip. Every other row still says where it stands: `stateTone="needs"`
   names what it is waiting on (this is the ONLY place in the app that appears),
   `"has"` confirms its inputs arrived. */
const STATE_GLYPH = { needs: "triangle-alert", has: "check" };

export function SectionRow({ num, name, state, stateTone, live = false, chip = "Open", sprite = "assets/icons/sprite.svg", onClick }) {
  const cls = [
    "rrf-sectionrow",
    live ? "rrf-sectionrow--live" : "rrf-sectionrow--soon",
    stateTone === "has" ? "rrf-sectionrow--done" : "",
  ].filter(Boolean).join(" ");
  const body = (
    <>
      <span className="rrf-sectionrow__num">{num}</span>
      <span>
        <span className="rrf-sectionrow__name">{name}</span>
        {state ? (
          <span className={`rrf-sectionrow__state${stateTone ? ` rrf-sectionrow__state--${stateTone}` : ""}`}>
            {STATE_GLYPH[stateTone] ? (
              <svg className="rrf-icon" aria-hidden="true"><use href={`${sprite}#${STATE_GLYPH[stateTone]}`} /></svg>
            ) : null}
            {state}
          </span>
        ) : null}
      </span>
      {live ? <Chip tone="live">{chip}</Chip> : null}
    </>
  );
  return live
    ? <button className={cls} onClick={onClick}>{body}</button>
    : <div className={cls}>{body}</div>;
}
