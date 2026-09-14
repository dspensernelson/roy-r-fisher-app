import React from "react";

/**
 * The small x that clears a message off the screen.
 *
 * Spenser, 2026-09-04, walking the photo screen: *"Imagine three or four of
 * these piling up."* He was right. The photo screen alone can show six boxes
 * at once, and none of them could be got rid of. They sat there until the
 * thing that put them up decided to change its mind.
 *
 * One control, in one file, so every message loses its x or keeps it by the
 * same rule rather than by whoever wrote that screen.
 *
 * **A message a person has to act on does not get one.** The x is for things
 * that have been read: what a run cost, what was made, what went wrong and has
 * been understood. It is never a way to make a question go away without
 * answering it.
 */
export default function CloseX({ onClose, what = "this message" }) {
  if (!onClose) return null;
  return (
    <button className="note-x" onClick={onClose}
            aria-label={`Close ${what}`} title="Close">
      &times;
    </button>
  );
}
