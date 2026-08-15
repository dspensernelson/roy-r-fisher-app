import React, { useEffect, useState } from "react";
import { jobDetail, scanJob } from "../api.js";

// The only section the app can build today. Everything else is listed so the
// report's real shape is visible, and says plainly that it is not ready yet.
const BUILDABLE = "Subject Photographs";

function list(words) {
  if (words.length <= 2) return words.join(" and ");
  return `${words.slice(0, -1).join(", ")}, and ${words[words.length - 1]}`;
}

export default function JobHome({ job, onOpenPhotos, onEditSections }) {
  const [detail, setDetail] = useState(null);
  const [folders, setFolders] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setError(null);
    setDetail(null);
    Promise.all([jobDetail(job), scanJob(job)])
      .then(([d, s]) => { setDetail(d); setFolders(s.folders); })
      .catch(() => setError("Could not reach the app's server. Close this tab and start the app again."));
  }, [job]);

  if (error) return (<><h1>{job}</h1><div className="error">{error}</div></>);
  if (!detail) return <p className="sub">Loading...</p>;

  const sections = detail.sections || [];
  const heading = [detail.context, detail.engagement].filter(Boolean).join(" · ");

  return (
    <>
      <h1>{job}</h1>
      <p className="sub">{heading || "No address recorded for this job yet."}</p>

      <div className="bands">
        <div>
          <div className="band-head">
            <h2>What has arrived</h2>
            <span className="note">read from your folders just now</span>
          </div>
          {(folders || []).map((f) => (
            <div className="folder" key={f.folder}>
              <div className="top">
                <span className="name">{f.folder}</span>
                <span className="count">{f.count} {f.count === 1 ? "file" : "files"}</span>
              </div>
              {f.here.length > 0 && <div className="line has">Has {list(f.here)}</div>}
              {f.needs.length > 0 && <div className="line needs">Still needs {list(f.needs)}</div>}
              {f.here.length === 0 && f.needs.length === 0 && (
                <div className="line quiet">Nothing this report needs comes from here</div>
              )}
            </div>
          ))}
        </div>

        <div>
          <div className="band-head">
            <h2>The report</h2>
            <span className="note">
              {sections.length > 0 ? `${sections.length} sections, in print order` : "not chosen yet"}
            </span>
            <button className="linky" onClick={onEditSections}>
              {sections.length > 0 ? "Change sections" : "Choose sections"}
            </button>
          </div>

          {/* Said once, quietly, instead of stamping a Not yet chip on
              sixteen rows. The dimmed rows already read as unavailable. */}
          {sections.length > 1 && (
            <p className="band-note">Subject Photographs is the only one that builds so far.</p>
          )}

          {sections.length === 0 && (
            <div className="empty-note">
              <div className="name">No sections chosen yet</div>
              <div className="state">
                Choose the sections this report needs and they will be listed here.
              </div>
            </div>
          )}

          {sections.map((name, i) =>
            name === BUILDABLE ? (
              <button className="section-row live" key={name} onClick={onOpenPhotos}>
                <span className="num">{i + 1}</span>
                <span>
                  <span className="name">{name}</span>
                  <span className="state">
                    {detail.photo_count} {detail.photo_count === 1 ? "photo" : "photos"} in the folder
                  </span>
                </span>
                <span className="chip">Open</span>
              </button>
            ) : (
              <div className="section-row soon" key={name}>
                <span className="num">{i + 1}</span>
                <span className="name">{name}</span>
              </div>
            )
          )}
        </div>
      </div>
    </>
  );
}
