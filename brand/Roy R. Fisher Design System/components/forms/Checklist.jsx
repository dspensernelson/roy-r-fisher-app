import React from "react";

/* The report's sections, checkable. Unchecked rows dim rather than disappear,
   so the shape of the whole report stays visible. */
export function Checklist({ items = [], checked = {}, onToggle }) {
  return (
    <div className="rrf-checklist">
      {items.map((name) => (
        <label key={name} className={`rrf-check${checked[name] ? "" : " is-off"}`}>
          <input type="checkbox" checked={!!checked[name]}
            onChange={(e) => onToggle && onToggle(name, e.target.checked)} />
          {name}
        </label>
      ))}
    </div>
  );
}
