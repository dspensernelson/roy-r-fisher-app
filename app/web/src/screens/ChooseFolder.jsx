import React, { useEffect, useState } from "react";
import { browseFolders, saveWorkspace } from "../api.js";

// Drawn in the app's own page. The computer's own folder window kept opening
// behind the browser on a Mac and there is no way to lift it, so this list
// replaces it. It cannot go behind anything, because it is not a window.
export default function ChooseFolder({ first, current, missing, onSaved, onCancel }) {
  const [loc, setLoc] = useState(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  const go = (path) => {
    setBusy("Reading..."); setError("");
    browseFolders(path)
      .then((r) => { setLoc(r); setBusy(""); })
      .catch((e) => { setError(e.message); setBusy(""); });
  };

  useEffect(() => { go(current || ""); }, []);

  async function use() {
    setBusy("Saving..."); setError("");
    try { onSaved(await saveWorkspace(loc.path)); }
    catch (e) { setError(e.message); setBusy(""); }
  }

  const folders = loc ? loc.folders : [];
  // What the server found here, and therefore whether this folder can be
  // confirmed at all. The button used to be live everywhere, including the
  // drive root and inside a single job.
  const jobsHere = loc && loc.readable && !loc.is_drive_list ? loc.job_count : 0;
  const canUse = jobsHere > 0;

  return (
    <>
      <div className="title-row">
        <h1>{first ? "Choose your jobs folder" : "Change jobs folder"}</h1>
        {!first && (
          <div className="title-actions">
            <button className="linky" onClick={onCancel} disabled={!!busy}>Cancel</button>
          </div>
        )}
      </div>

      {first
        ? <p className="sub">Click through to the folder your job folders sit in. The app remembers it.</p>
        : <p className="sub">The app is pointed at <strong>{current}</strong> right now.</p>}

      {missing && (
        <div className="error">
          The folder this app was pointed at is not there any more:<br />
          <strong>{missing}</strong><br />
          It may have been moved or renamed. Nothing has been changed or deleted.
        </div>
      )}
      {error && <div className="error">{error}</div>}

      {loc && (
        <>
          <nav className="crumbs">
            {loc.breadcrumbs.map((c, i) => (
              <React.Fragment key={c.path}>
                {i > 0 && <span className="crumb-sep">›</span>}
                <button className="crumb" onClick={() => go(c.path)}>{c.label || "/"}</button>
              </React.Fragment>
            ))}
          </nav>

          {/* The result of looking in here, and the action that acts on it,
              in one place. The count is the whole decision, so the button
              that depends on it sits beside the count rather than at the far
              edge of the screen. */}
          {loc.readable ? (
            <div className={`folder-result${canUse ? " is-ready" : ""}`}>
              <div>
                <strong className="folder-result-count">
                  {jobsHere === 0
                    ? "No jobs found here"
                    : `${jobsHere} ${jobsHere === 1 ? "job" : "jobs"} found`}
                </strong>
                <span className="folder-result-note">
                  {canUse
                    ? "This is the folder your jobs sit in. Stop here and choose it."
                    : "Open one of the folders below to keep looking."}
                </span>
              </div>
              {/* No title when it is off. A tooltip becomes the button's
                  accessible name, so it announced the reason instead of
                  "Use this folder". The reason is already in the note beside
                  it, where it can be read rather than hovered for. */}
              <button className={`button${canUse ? "" : " is-off"}`} onClick={use}
                      disabled={!canUse || !!busy}>
                Use this folder
              </button>
            </div>
          ) : (
            <p className="sub">{loc.message}</p>
          )}

          {loc.readable && (
            <p className="sub">
              {folders.length} {folders.length === 1 ? "folder is" : "folders are"} directly
              inside this one
              {loc.loose_files > 0 && <>, beside {loc.loose_files} loose{" "}
                {loc.loose_files === 1 ? "file that is not a job" : "files that are not jobs"}</>}.
            </p>
          )}

          <div className="picker">
            {loc.parent !== null && (
              <button className="picker-row up" onClick={() => go(loc.parent)}
                      aria-label="Up one folder">
                <span className="picker-icon" aria-hidden="true">↑</span>
                <span className="picker-name">Up one folder</span>
              </button>
            )}
            {/* Named for a screen reader and for the keyboard. The row used to
                announce itself as an unlabelled button, because the only text
                in it sat inside a span the icon shared. */}
            {folders.map((f) => (
              <button className="picker-row" key={f.path} onClick={() => go(f.path)}
                      aria-label={f.is_job ? `Open job folder ${f.name}` : `Open folder ${f.name}`}>
                <span className="picker-icon" aria-hidden="true">▸</span>
                <span className="picker-name">{f.name}</span>
                {f.is_job && <span className="picker-tag">job</span>}
              </button>
            ))}
            {loc.readable && folders.length === 0 && (
              <p className="picker-empty">This folder contains no folders.</p>
            )}
          </div>
        </>
      )}

      {busy && (
        <div className="working">
          <span className="loading-bar"><span /></span>
          <span className="working-text">{busy}</span>
        </div>
      )}
    </>
  );
}
