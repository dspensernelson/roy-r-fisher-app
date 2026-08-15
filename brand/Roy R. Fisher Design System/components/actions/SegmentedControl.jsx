import React from "react";

/* Two or three equal halves, short. Used as a step inside the action it
   shapes — the caption chooser sits at the head of the caption column. An
   option may carry a `flag` ("suggested"), which renders as a small ruled
   caption ABOVE the control, over the option it recommends — not as a second
   word inside the button. */
export function SegmentedControl({ options = [], value, onChange }) {
  return (
    <div className="rrf-seg" role="tablist">
      {options.map((o) => (
        <button key={o.key} role="tab" aria-selected={value === o.key}
          className={`rrf-seg__btn${value === o.key ? " is-on" : ""}`}
          onClick={() => onChange && onChange(o.key)}>
          {o.flag ? <span className="rrf-seg__flag">{o.flag}</span> : null}
          <span>{o.label}</span>
        </button>
      ))}
    </div>
  );
}
