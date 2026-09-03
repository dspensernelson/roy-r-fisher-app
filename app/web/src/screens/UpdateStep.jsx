import React, { useEffect, useRef, useState } from "react";
import { startUpdate, updateProgress, cancelUpdate } from "../api.js";

// What a new version costs him, said before he agrees to it. The size comes
// from the bucket, so it is the real number and not a guess.
export function megabytes(bytes) {
  if (!bytes || bytes < 0) return "";
  return `${Math.round(bytes / (1024 * 1024))} MB`;
}

// How often the screen asks how the run is going. Often enough that a 53 MB
// download visibly moves, rare enough that it is not asking constantly.
const POLL_MS = 700;

/**
 * The step behind the "Update available" button.
 *
 * A click leads to a step: he clicks the notice, and the question about
 * whether to update is asked here, inside the action, rather than parked on a
 * screen beside it.
 *
 * Three states, in order. What it costs and whether to do it. Then how far it
 * has got. Then, if it worked, what is about to happen. A failure replaces all
 * of them with one sentence and leaves the app underneath it working.
 */
export default function UpdateStep({ version, available, size, onClose }) {
  const [run, setRun] = useState(null);
  const [error, setError] = useState("");
  const [started, setStarted] = useState(false);
  const timer = useRef(null);

  useEffect(() => () => clearTimeout(timer.current), []);

  function poll() {
    updateProgress()
      .then((found) => {
        setRun(found);
        if (found.running) timer.current = setTimeout(poll, POLL_MS);
      })
      // The app closing itself is the successful ending, and the last poll
      // before it goes will fail to answer. That is not an error to report:
      // whatever the run was doing stays on screen.
      .catch(() => { /* the app is going, which is what was asked for */ });
  }

  async function onStart() {
    setError(""); setStarted(true);
    try {
      await startUpdate();
      poll();
    } catch (e) {
      setStarted(false);
      setError(e.message);
    }
  }

  const stage = run && run.stage;
  const closing = stage === "Closing";
  const failed = run && run.error;

  if (failed) {
    return (
      <div className="confirm update-step">
        <div className="error" style={{ whiteSpace: "pre-line" }}>{run.error}</div>
        <div className="setting-actions">
          <button className="linky" onClick={onClose}>Close</button>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="confirm update-step">
        <div className="error">{error}</div>
        <div className="setting-actions">
          <button className="linky" onClick={onClose}>Close</button>
        </div>
      </div>
    );
  }

  if (closing) {
    // Over everything, not laid on top of a job list that still looks usable.
    //
    // Found on Spenser's virtual machine, 2026-09-03. This used to be a small
    // panel above the jobs, and the moment the server stopped, the browser
    // simply kept showing whatever it had last drawn: this sentence, sitting
    // on a screen full of jobs that could no longer be opened. The last thing
    // the app did before handing over was look broken.
    //
    // Nothing here can poll for the new version. It arrives on a port the
    // operating system picks, in a tab of its own, and this page has no
    // server left to ask. So it says what will happen and what to do if it
    // does not, and it stops pretending anything behind it still works.
    return (
      <div className="closing-over-everything">
        <div className="closing-card">
          <p className="closing-title">Installing the new version.</p>
          <span className="loading-bar"><span /></span>
          <p className="setting-fine" style={{ margin: "14px 0 0" }}>
            The app has closed itself so its files can be replaced. The new
            version opens in a new tab in a few seconds.
          </p>
          <p className="setting-fine" style={{ margin: "10px 0 0" }}>
            <strong>You can close this tab.</strong> If nothing opens, use the
            Roy R. Fisher icon on your Desktop.
          </p>
        </div>
      </div>
    );
  }

  if (started && run && run.running) {
    const done = run.done || 0;
    const total = run.total || 0;
    const pct = total ? Math.min(100, Math.round((done / total) * 100)) : 0;
    const downloading = stage === "Downloading";
    return (
      <div className="confirm update-step">
        <p style={{ margin: "0 0 10px" }}>
          <strong>
            {downloading && total
              ? `Downloading ${megabytes(done)} of ${megabytes(total)}`
              : stage}
          </strong>
        </p>
        <span className="loading-bar update-bar">
          <span style={downloading && total ? { width: `${pct}%` } : undefined} />
        </span>
        {downloading && (
          <div className="setting-actions" style={{ marginTop: 12 }}>
            <button className="linky" disabled={run.cancelling}
                    onClick={() => cancelUpdate().catch(() => {})}>
              {run.cancelling ? "Stopping..." : "Cancel"}
            </button>
          </div>
        )}
      </div>
    );
  }

  if (started) {
    return (
      <div className="confirm update-step">
        <p style={{ margin: 0 }}><strong>Starting...</strong></p>
      </div>
    );
  }

  return (
    <div className="confirm update-step">
      <p style={{ margin: "0 0 10px" }}>
        <strong>Update to version {available}?</strong>
      </p>
      <p className="setting-fine" style={{ margin: "0 0 8px" }}>
        You are on version {version}. The download is about {megabytes(size)}.
        The app will close itself and open again as the new version. Your key,
        your jobs folder, your settings and every document you have built are
        not kept inside the app and are not touched.
      </p>
      <p className="setting-fine" style={{ margin: "0 0 12px" }}>
        The app checks that what arrives is exactly what was published. That
        catches a damaged or incomplete download. It does not prove who made
        the file. If anything goes wrong, nothing is changed and the version
        you have now is not touched.
      </p>
      <div className="setting-actions">
        <button className="button" onClick={onStart}>Update now</button>
        <button className="linky" onClick={onClose}>Not now</button>
      </div>
    </div>
  );
}
