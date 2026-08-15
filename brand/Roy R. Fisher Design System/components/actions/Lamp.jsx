import React from "react";

/* On or off, plainly. Used on settings cards so the state is readable without
   interpreting a switch. */
export function Lamp({ state = "off", labels = { on: "On", off: "Off", busy: "Checking" } }) {
  return <span className={`rrf-lamp rrf-lamp--${state}`}>{labels[state]}</span>;
}
