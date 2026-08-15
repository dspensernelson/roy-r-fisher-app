import React from "react";
import { Chip } from "../actions/Chip.jsx";

/* One thing to do, on the job worklist. `next` marks the single top task with
   the red rule — six red rules would be wallpaper, and the group heading
   already says the whole group is doable. `tone="done"` is a thing already in
   the folder, kept visible because it is reassurance, not a task. */
export function TaskRow({ icon, name, why, chip, tone = "do", next = false, sprite = "assets/icons/sprite.svg", onClick }) {
  const cls = ["rrf-task", next ? "rrf-task--next" : "", tone === "done" ? "rrf-task--done" : ""].filter(Boolean).join(" ");
  const glyph = icon || (tone === "done" ? "check" : "folder");
  const body = (
    <>
      <svg className={`rrf-icon rrf-icon--lg ${tone === "done" ? "rrf-icon--has" : "rrf-icon--quiet"}`} aria-hidden="true">
        <use href={`${sprite}#${glyph}`} />
      </svg>
      <span className="rrf-task__body">
        <span className="rrf-task__name">{name}</span>
        {why ? <span className="rrf-task__why">{why}</span> : null}
      </span>
      {chip ? <Chip tone="live">{chip}</Chip> : null}
    </>
  );
  return tone === "done"
    ? <div className={cls}>{body}</div>
    : <button className={cls} onClick={onClick}>{body}</button>;
}
