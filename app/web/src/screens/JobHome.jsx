import React, { useEffect, useState } from "react";
import {
  jobDetail, jobFolders, classificationLabels,
  setClassification, clearClassification,
} from "../api.js";

// The only section the app can build today. Everything else is listed so the
// report's real shape is visible, and says plainly that it is not ready yet.
const BUILDABLE = "Subject Photographs";

// What a folder row is allowed to say about itself. A shortcut is not opened
// and an unreadable folder is not guessed at, so neither gets a file count.
function folderNote(f) {
  if (f.kind === "shortcut") return "shortcut, not opened";
  if (f.unreadable) return "could not be read";
  return `${f.count} ${f.count === 1 ? "file" : "files"}`;
}

function FileRow({ file, labels, onPick, onClear, busy }) {
  const [picking, setPicking] = useState(false);
  // A refusal belongs on the row he clicked, not across the whole screen. The
  // screen-level error replaces the job with one sentence, which is right when
  // the server has gone and wrong when one file cannot be one label.
  const [refused, setRefused] = useState("");
  const chosen = file.classification;
  const gone = file.kind === "missing";
  const link = file.kind === "shortcut";

  return (
    <div className="file">
      <div className="file-top">
        <span className={gone ? "file-name gone" : "file-name"}>{file.name}</span>
        {file.within && <span className="file-where">in {file.within}</span>}
        {link && <span className="file-where">shortcut, not read</span>}

        {chosen && (
          <span className="file-said">
            {chosen.label}
            {chosen.state === "present" && ", confirmed by you"}
            {chosen.state === "changed" && ", but this file has changed since you confirmed it"}
            {chosen.state === "missing" && ", but this file is no longer in the folder"}
          </span>
        )}

        {!link && (
          <span className="file-acts">
            {!gone && (
              <button className="linky" disabled={busy}
                      onClick={() => { setRefused(""); setPicking(!picking); }}>
                {chosen ? "Change" : "Classify"}
              </button>
            )}
            {chosen && (
              <button className="linky" disabled={busy}
                      onClick={() => { setPicking(false); onClear(file.rel); }}>
                Remove
              </button>
            )}
          </span>
        )}
      </div>

      {/* The choice lives inside the action, asked when he clicks it, rather
          than parked on the page beside it. */}
      {/* Said where he clicked, in the app's own words, and nothing was
          written down. */}
      {refused && <div className="file-refused">{refused}</div>}

      {picking && (
        <div className="say-what">
          {labels.map((label) => (
            <button key={label} disabled={busy}
                    onClick={() => {
                      setPicking(false);
                      setRefused("");
                      onPick(file.rel, label).catch((e) => setRefused(e.message));
                    }}>
              {label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function FolderRow({ f, open, onToggle, labels, onPick, onClear, busy }) {
  const openable = f.kind !== "shortcut" && !f.unreadable && f.files.length > 0;
  // A folder with nothing in it is still worth listing, because the row is how
  // he sees the shape of a job. It is not worth the same weight as one holding
  // his photographs. Seven of these at full strength were drowning the one
  // action on the screen.
  const empty = f.kind !== "shortcut" && !f.unreadable && f.count === 0;
  return (
    <div className={`folder${empty ? " is-empty" : ""}`}>
      <div className="top">
        {openable ? (
          <button className="folder-open" onClick={() => onToggle(f.folder)}>
            <span className="caret">{open ? "▾" : "▸"}</span>
            <span className="name">{f.folder}</span>
          </button>
        ) : (
          <span className="name">{f.folder}</span>
        )}
        <span className="count">{folderNote(f)}</span>
      </div>
      {open && f.files.map((file) => (
        <FileRow key={file.rel} file={file} labels={labels}
                 onPick={onPick} onClear={onClear} busy={busy} />
      ))}
    </div>
  );
}

export default function JobHome({ job, onOpenPhotos, onEditSections }) {
  const [detail, setDetail] = useState(null);
  const [found, setFound] = useState(null);
  const [labels, setLabels] = useState([]);
  const [open, setOpen] = useState({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const reachError = "Could not reach the app's server. Close this tab and start the app again.";

  useEffect(() => {
    setError(null);
    setDetail(null);
    Promise.all([jobDetail(job), jobFolders(job), classificationLabels()])
      .then(([d, f, l]) => { setDetail(d); setFound(f); setLabels(l.labels); })
      .catch(() => setError(reachError));
  }, [job]);

  function refresh() {
    return jobFolders(job).then(setFound);
  }

  function pick(file, label) {
    setBusy(true);
    // Returned rather than swallowed, so the row that was clicked can show
    // what the app said instead of the whole screen being replaced by it.
    return setClassification(job, file, label)
      .then(refresh)
      .finally(() => setBusy(false));
  }

  function clear(file) {
    setBusy(true);
    clearClassification(job, file)
      .then(refresh)
      .catch((e) => setError(e.message || reachError))
      .finally(() => setBusy(false));
  }

  function toggle(name) {
    setOpen((was) => ({ ...was, [name]: !was[name] }));
  }

  if (error) return (<><h1>{job}</h1><div className="error">{error}</div></>);
  if (!detail || !found) return <p className="sub">Loading...</p>;

  const sections = detail.sections || [];
  const heading = [detail.context, detail.engagement].filter(Boolean).join(" · ");
  const rowProps = { labels, onPick: pick, onClear: clear, busy };

  return (
    <>
      <h1>{job}</h1>
      <p className="sub">{heading || "No address recorded for this job yet."}</p>

      <div className="bands">
        <div>
          <div className="band-head">
            <h2>What is in your folders</h2>
            <span className="note">read from your folders just now</span>
          </div>

          {found.typical.map((f) => (
            <FolderRow key={f.folder} f={f} open={!!open[f.folder]}
                       onToggle={toggle} {...rowProps} />
          ))}

          {found.other.length > 0 && (
            <>
              <div className="band-head sub-head"><h2>Other folders found</h2></div>
              {found.other.map((f) => (
                <FolderRow key={f.folder} f={f} open={!!open[f.folder]}
                           onToggle={toggle} {...rowProps} />
              ))}
            </>
          )}

          {/* Neither of these is a folder, so neither sits under the folder
              headings and neither collapses. They are short, and the second
              one is the only place a record whose folder has gone can be
              reached at all. */}
          {found.root_files.length > 0 && (
            <>
              <div className="band-head sub-head"><h2>Loose files in the job folder</h2></div>
              <div className="folder">
                {found.root_files.map((file) => (
                  <FileRow key={file.rel} file={file} {...rowProps} />
                ))}
              </div>
            </>
          )}

          {found.missing_classifications.length > 0 && (
            <>
              <div className="band-head sub-head">
                <h2>Classified files whose source is missing</h2>
              </div>
              <div className="folder">
                {found.missing_classifications.map((file) => (
                  <FileRow key={file.rel} file={file} {...rowProps} />
                ))}
              </div>
            </>
          )}
        </div>

        {/* Photos is the whole pilot. The section picker is bypassed rather
            than deleted: `sections` and the chooser screen still exist behind
            this, because Phase 2 multiplies sections and rebuilding the
            machinery then would be worse than hiding it now.

            Approved 2026-08-20. Mark does not choose report sections, does not
            see a multi-section configuration step, and does not meet an empty
            "no sections chosen yet" state before he can do the one thing the
            app does. He opens a job and Photos is there. */}
        <div>
          <div className="band-head">
            <h2>The report</h2>
            <span className="note">Subject Photographs</span>
          </div>

          <button className="section-row live" onClick={onOpenPhotos}>
            <span className="num">1</span>
            <span>
              <span className="name">{BUILDABLE}</span>
              <span className="state">
                {/* What this section holds now, which is what would build.
                    Not the number of files in the folder: after he picks a
                    folder those are different numbers, and the Photos screen
                    shows the other one. */}
                {detail.photo_count} {detail.photo_count === 1 ? "photo" : "photos"}
              </span>
            </span>
            <span className="chip">Open</span>
          </button>
        </div>
      </div>

      {/* One band at the bottom, below the folder bands, holding one plain
          row. Nothing here is a control: it does not respond to a click, it
          carries no button styling, and it sits below everything that works
          so it cannot be mistaken for part of the workflow. The actions on
          this screen live at the top on the title's row.

          Deliberately not "Coming soon", and deliberately with no date. The
          row says what is true today and promises nothing. */}
      <div className="bands">
        <div className="band planned">
          <div className="band-head sub-head"><h2>Planned workflows</h2></div>
          <p className="band-note">
            Not part of this pilot. Listed so the report's real shape is visible.
          </p>
          <div className="planned-row" aria-disabled="true">
            <span className="name">Description of Improvements</span>
            <span className="planned-state">Not available in this pilot</span>
          </div>
        </div>
      </div>
    </>
  );
}
