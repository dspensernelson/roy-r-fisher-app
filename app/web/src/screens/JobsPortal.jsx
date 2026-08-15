import React, { useEffect, useState } from "react";
import { listJobs, getWorkspaceFolders, putWorkspaceFolders } from "../api.js";

export default function JobsPortal({ onOpen, onNew, onChangeFolder, onManage }) {
  const [jobs, setJobs] = useState(null);
  const [error, setError] = useState(null);
  const [menu, setMenu] = useState(null);     // which card's ellipsis is open
  const refresh = () => listJobs().then((j) => { setJobs(j); setError(null); })
    .catch(() => setError("Could not reach the app's server. Close this tab and start the app again."));
  useEffect(() => { refresh(); }, []);

  // Closing a menu by clicking anywhere else, the way every menu he uses works.
  useEffect(() => {
    if (!menu) return;
    const away = () => setMenu(null);
    window.addEventListener("click", away);
    return () => window.removeEventListener("click", away);
  }, [menu]);

  async function makeNotActive(name) {
    setMenu(null);
    try {
      const listed = await getWorkspaceFolders();
      await putWorkspaceFolders(listed.active.filter((n) => n !== name));
      refresh();
    } catch (e) { setError(e.message); }
  }

  return (
    <>
      <div className="title-row">
        <h1>Jobs</h1>
        <div className="title-actions">
          <button className="linky" onClick={onManage}>Manage active jobs</button>
          <button className="linky" onClick={onChangeFolder}>Change jobs folder</button>
        </div>
      </div>
      <p className="sub">The jobs you are working on. Click one to open it.</p>
      {error && <div className="error">{error}</div>}

      {jobs && jobs.length === 0 && !error && (
        <p className="sub">
          No job is active yet. <button className="linky inline" onClick={onManage}>
          Manage active jobs</button> to pick the ones you are working on.
        </p>
      )}

      <div className="cards">
        {(jobs || []).map((job) => (
          <div className="card" key={job.name}>
            {/* The whole tile opens the job. The ellipsis sits on top of it as
                its own control, because a button inside a button is not a
                thing a browser will do. */}
            <button className="card-open" onClick={() => onOpen(job.name)}>
              <div className="addr">{job.name}</div>
              <div className="meta">{job.photo_count} photos</div>
            </button>
            <button className="card-more" title="More"
              onClick={(e) => { e.stopPropagation(); setMenu(menu === job.name ? null : job.name); }}>
              ···
            </button>
            {menu === job.name && (
              <div className="card-menu" onClick={(e) => e.stopPropagation()}>
                <button onClick={() => makeNotActive(job.name)}>Make not active</button>
              </div>
            )}
          </div>
        ))}
        {!error && <button className="card new" onClick={onNew}>+ New job</button>}
      </div>
    </>
  );
}
