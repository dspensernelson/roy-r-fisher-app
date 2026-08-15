import React from "react";

/* The right-hand end of a row. `live` is an outlined blue pill — the word is
   the affordance; red is spent on the letterhead band and the primary button.
   `default` and `quiet` are grey; `done` and `needs` carry state tints. */
export function Chip({ tone = "default", children }) {
  return <span className={`rrf-chip${tone === "default" ? "" : ` rrf-chip--${tone}`}`}>{children}</span>;
}
