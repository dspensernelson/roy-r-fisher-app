import React, { useEffect, useMemo, useState } from "react";
import { getWorkspaceFolders, putWorkspaceFolders } from "../api.js";

// Every folder that is actually in his jobs folder, by its exact name. His
// real one holds jobs going back years, so this is a searchable list in a
// box that scrolls, not five hundred cards down a page. Nothing starts
// selected: he says what he is working on, the app never assumes.
export default function ActiveJobs({ first, onDone, onCancel }) {
  const [data, setData] = useState(null);
  const [chosen, setChosen] = useState(null);   // a Set, once loaded
  const [find, setFind] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    getWorkspaceFolders()
      .then((r) => { setData(r); setChosen(new Set(r.active)); })
      .catch((e) => setError(e.message));
  }, []);

  const shown = useMemo(() => {
    if (!data) return [];
    const needle = find.trim().toLowerCase();
    if (!needle) return data.folders;
    return data.folders.filter((n) => n.toLowerCase().includes(needle));
  }, [data, find]);

  function toggle(name) {
    const next = new Set(chosen);
    if (next.has(name)) next.delete(name); else next.add(name);
    setChosen(next);
  }

  // Both of these change what is on screen and nothing else. Nothing is
  // written until Use these active jobs is pressed, so a mis-click costs a
  // second click rather than his selection. Select all means every folder in
  // the parent, never just the ones a search happens to be showing: a button
  // that says 500 and selects 3 would be lying.
  const selectAll = () => setChosen(new Set(data.folders));
  const clearAll = () => setChosen(new Set());

  async function save() {
    setBusy("Saving..."); setError("");
    try { await putWorkspaceFolders([...chosen]); onDone(); }
    catch (e) { setError(e.message); setBusy(""); }
  }

  if (error && !data) return (<><h1>Active jobs</h1><div className="error">{error}</div></>);
  if (!data) return <p className="sub">Loading...</p>;

  return (
    <>
      <div className="title-row">
        <h1>{first ? "Which jobs are you working on?" : "Manage active jobs"}</h1>
        <div className="title-actions">
          {/* Off at zero. It used to be live with nothing ticked, and pressing
              it produced a Jobs screen with nothing on it and no explanation
              of why. Nothing starts selected, which is unchanged: he says
              what he is working on and the app never assumes. */}
          <button className={`button${chosen.size === 0 ? " is-off" : ""}`}
                  onClick={save} disabled={!!busy || chosen.size === 0}
                  title={chosen.size === 0 ? "Pick at least one job to work on" : ""}>
            Use these active jobs
          </button>
          {!first && <button className="linky" onClick={onCancel} disabled={!!busy}>Cancel</button>}
        </div>
      </div>

      <p className="sub">
        Every folder in <strong>{data.parent}</strong>, spelled as it is on disk.
        Click the ones you are working on now. The others stay exactly where they are.
      </p>

      {data.missing.length > 0 && (
        <div className="error">
          {data.missing.length === 1 ? "A folder you had active is" : "Folders you had active are"}
          {" "}no longer in this folder:{" "}
          <strong>{data.missing.join(", ")}</strong>.
          {" "}They may have been renamed or moved. Nothing has been changed or deleted.
        </div>
      )}
      {error && <div className="error">{error}</div>}

      <div className="picker-head">
        <input className="find" type="search" value={find} placeholder="Find a job by name"
          onChange={(e) => setFind(e.target.value)} />
        <button className="linky inline" onClick={selectAll}
          disabled={chosen.size === data.folders.length || data.folders.length === 0}>
          Select all {data.folders.length} {data.folders.length === 1 ? "job" : "jobs"}
        </button>
        <button className="linky inline" onClick={clearAll} disabled={chosen.size === 0}>
          Clear all
        </button>
        <span className={`count${chosen.size === 0 ? " is-none" : " is-some"}`}>
          {chosen.size} of {data.folders.length} active
          {find.trim() && shown.length !== data.folders.length &&
            <> · showing {shown.length}</>}
        </span>
      </div>

      <div className="picker tall">
        {shown.map((name) => (
          <button key={name} className={`picker-row pick ${chosen.has(name) ? "on" : ""}`}
            onClick={() => toggle(name)}>
            <span className="tick">{chosen.has(name) ? "✓" : ""}</span>
            <span className="picker-name">{name}</span>
          </button>
        ))}
        {shown.length === 0 && (
          <p className="picker-empty">
            {data.folders.length === 0
              ? "This folder contains no folders."
              : "No folder here has that in its name."}
          </p>
        )}
      </div>

      {chosen.size === 0 && (
        <p className="pick-required">
          Pick at least one job to carry on. The others stay exactly where they are,
          and you can change this later.
        </p>
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
