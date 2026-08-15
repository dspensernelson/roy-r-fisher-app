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

  return (
    <>
      <div className="title-row">
        <h1>{first ? "Choose your jobs folder" : "Change jobs folder"}</h1>
        <div className="title-actions">
          {loc && loc.readable && !loc.is_drive_list && (
            <button className="button" onClick={use} disabled={!!busy}>Use this folder</button>
          )}
          {!first && <button className="linky" onClick={onCancel} disabled={!!busy}>Cancel</button>}
        </div>
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

          {/* What is actually in here, read now. This is the preview: he is
              looking at the real contents before he commits to anything. */}
          <p className="sub">
            {loc.readable
              ? <>
                  {folders.length} {folders.length === 1 ? "folder is" : "folders are"} directly
                  inside this one
                  {loc.loose_files > 0 && <>, beside {loc.loose_files} loose{" "}
                    {loc.loose_files === 1 ? "file that is not a job" : "files that are not jobs"}</>}.
                </>
              : loc.message}
          </p>

          <div className="picker">
            {loc.parent !== null && (
              <button className="picker-row up" onClick={() => go(loc.parent)}>
                <span className="picker-icon">↑</span>
                <span className="picker-name">Up one folder</span>
              </button>
            )}
            {folders.map((f) => (
              <button className="picker-row" key={f.path} onClick={() => go(f.path)}>
                <span className="picker-icon">▸</span>
                <span className="picker-name">{f.name}</span>
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
