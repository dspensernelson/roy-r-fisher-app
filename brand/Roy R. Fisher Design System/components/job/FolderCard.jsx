import React from "react";

/* One folder from the job directory, read just now. The has/needs distinction
   is the point of the row: green for what arrived, amber for what the report
   still wants, italic grey when the folder feeds nothing this report needs. */
export function FolderCard({ folder, count, has = [], needs = [], sprite = "assets/icons/sprite.svg" }) {
  const glyph = (n) => <svg className="rrf-icon" aria-hidden="true"><use href={`${sprite}#${n}`} /></svg>;
  const list = (w) => (w.length <= 2 ? w.join(" and ") : `${w.slice(0, -1).join(", ")}, and ${w[w.length - 1]}`);
  return (
    <div className="rrf-folder">
      <div className="rrf-folder__top">
        <span className="rrf-folder__name">{folder}</span>
        <span className="rrf-folder__count">{count} {count === 1 ? "file" : "files"}</span>
      </div>
      {has.length > 0 ? <div className="rrf-folder__line rrf-folder__line--has">{glyph("check")}<span>Has {list(has)}</span></div> : null}
      {needs.length > 0 ? <div className="rrf-folder__line rrf-folder__line--needs">{glyph("triangle-alert")}<span>Still needs {list(needs)}</span></div> : null}
      {has.length === 0 && needs.length === 0 ? (
        <div className="rrf-folder__line rrf-folder__line--quiet">Nothing this report needs comes from here</div>
      ) : null}
    </div>
  );
}
