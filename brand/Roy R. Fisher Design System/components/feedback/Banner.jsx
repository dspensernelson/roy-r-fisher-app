import React from "react";

/* Four tones. The tinted ground makes a message impossible to miss; the glyph
   says which kind it is without relying on colour alone. `done` reports what
   was created and what was not overwritten; `error` says what to do next in
   plain words; `warn` flags thin evidence; `note` is a neutral aside. */
const GLYPH = { done: "check", error: "triangle-alert", warn: "triangle-alert", note: null };

export function Banner({ tone = "note", children, sprite = "assets/icons/sprite.svg", style }) {
  const glyph = GLYPH[tone];
  return (
    <div className={`rrf-banner rrf-banner--${tone}`} style={style}>
      {glyph ? <svg className="rrf-icon" aria-hidden="true"><use href={`${sprite}#${glyph}`} /></svg> : null}
      <span className="rrf-banner__text">{children}</span>
    </div>
  );
}
