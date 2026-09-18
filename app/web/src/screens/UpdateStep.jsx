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

// How often the closing tab asks whether the new version is up yet. The old
// app is gone by then, so these are requests to nothing until the new one
// answers, and a failed request to a dead port on your own machine is
// instant and free.
const WATCH_MS = 1000;

// How long it watches in silence before it says anything at all.
//
// Spenser chose three minutes on 2026-09-16, and the reason it is that long
// rather than ten seconds: an update unpacks and copies sixty megabytes and
// then starts a cold Python, and a slow office machine genuinely takes
// minutes. Anything said before the work can possibly have finished is the
// app claiming to know something it does not.
const PATIENCE_MS = 180 * 1000;

/**
 * The update run itself: starting it, following it, and watching for the new
 * version once the old one closes.
 *
 * Held by the app, not by the screen that draws it. Since 2026-09-18 the
 * update is drawn inside the version card on Settings (Spenser: "the whole
 * update should take place in the update box, not above the settings"), and a
 * card is gone the moment he opens a job. If the run lived in the card,
 * leaving Settings mid-download would stop the poll and the watch, and this
 * tab would never become the new version. So the run lives up here and the
 * card only draws it.
 */
export function useUpdateRun(version) {
  const [run, setRun] = useState(null);
  const [error, setError] = useState("");
  const [started, setStarted] = useState(false);
  const [stuck, setStuck] = useState(false);
  const timer = useRef(null);

  useEffect(() => () => clearTimeout(timer.current), []);

  const closing = !!(run && run.stage === "Closing");

  // Watch for the new version on the address this tab already has, and become
  // it. This is the whole reason the app now answers on the same number every
  // time: this tab cannot be told anything once the old app exits, but it can
  // keep asking the one address it already knows.
  //
  // It insists on a version different from the one running. Something
  // answering is not enough, because the old app answers right up until it
  // goes, and reloading into it would put her back where she started.
  useEffect(() => {
    if (!closing) return undefined;
    let stop = false;
    const giveUp = setTimeout(() => { if (!stop) setStuck(true); }, PATIENCE_MS);
    let again = null;

    const look = () => {
      fetch("/api/version", { cache: "no-store" })
        .then((answer) => (answer.ok ? answer.json() : null))
        .then((found) => {
          if (stop || !found || !found.version || found.version === version) {
            throw new Error("not yet");
          }
          // Tell it we arrived, on the same route the loading page uses, so
          // it does not open a tab of its own beside this one. Then become
          // the new version. `replace` rather than `reload`: this tab's
          // history should not offer a Back button to a dead app.
          return fetch("/api/loading-page", { cache: "no-store" })
            .catch(() => null)
            .then(() => { window.location.replace("/"); });
        })
        .catch(() => { if (!stop) again = setTimeout(look, WATCH_MS); });
    };
    again = setTimeout(look, WATCH_MS);

    return () => {
      stop = true;
      clearTimeout(giveUp);
      clearTimeout(again);
    };
  }, [closing, version]);

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

  async function start() {
    setError(""); setStarted(true);
    try {
      await startUpdate();
      poll();
    } catch (e) {
      setStarted(false);
      setError(e.message);
    }
  }

  // Back to nothing, after a failure he has read and closed. Only ever
  // called when nothing is running.
  function reset() {
    clearTimeout(timer.current);
    setRun(null); setError(""); setStarted(false); setStuck(false);
  }

  return { run, error, started, stuck, closing, start, reset };
}

/**
 * The update's last screen, over everything.
 *
 * Found on Spenser's virtual machine, 2026-09-03. This used to be a small
 * panel above the jobs, and the moment the server stopped, the browser simply
 * kept showing whatever it had last drawn: this sentence, sitting on a screen
 * full of jobs that could no longer be opened. The last thing the app did
 * before handing over was look broken.
 *
 * It stays full screen after the rest of the update moved into the version
 * card on 2026-09-18, for that same reason: by now the app is closing under
 * it, and every card, button and job behind it has stopped working. A cover
 * inside one card would leave the rest of the screen looking alive.
 *
 * This tab is not a dead end any more. Since 2026-09-16 the app answers on
 * the same number every time, so this page can keep asking the one address it
 * already knows until the new version answers, and then become it. The effect
 * for her is a screen that blanks for a moment and comes back as the new
 * version. One tab, and nothing to close.
 *
 * It says nothing for three minutes. Spenser chose that length: an update
 * copies sixty megabytes and starts a cold Python, and a sentence that
 * arrives while that is still happening is the app claiming to know something
 * it does not.
 *
 * The sentence it finally shows promises no other window, because from in
 * here "the new app is somewhere else" and "the new app never started" are
 * the same silence. The Desktop icon is true in both cases: it stops anything
 * running and opens the app.
 */
export function UpdateCover({ stuck }) {
  return (
    <div className="closing-over-everything">
      <div className="closing-card">
        <p className="closing-title">Installing the new version.</p>
        <span className="loading-bar"><span /></span>
        {stuck ? (
          <p className="setting-fine" style={{ margin: "14px 0 0" }}>
            <strong>Roy R. Fisher is not answering.</strong> Open it from the
            Desktop icon to carry on.
          </p>
        ) : (
          <p className="setting-fine" style={{ margin: "14px 0 0" }}>
            This page comes back on its own when the new version is ready.
          </p>
        )}
      </div>
    </div>
  );
}

/**
 * The step behind the "Update available" button, drawn from a run it is
 * handed.
 *
 * A click leads to a step: he clicks the notice, and the question about
 * whether to update is asked here, inside the action, rather than parked on a
 * screen beside it.
 *
 * Three states, in order. What it costs and whether to do it. Then how far it
 * has got. Then, if it worked, what is about to happen, which is the cover
 * above and is not drawn here. A failure replaces all of them with one
 * sentence and leaves the app underneath it working.
 *
 * `inCard` draws it as part of the Settings card it sits in, with no box of
 * its own. Without it, it keeps the confirm box, for the two setup screens
 * that have no Settings to go to.
 */
export function UpdateStepView({ version, available, size, onClose, runner, inCard }) {
  const { run, error, started } = runner;
  const box = inCard ? "update-step in-card" : "confirm update-step";

  const stage = run && run.stage;
  const failed = run && run.error;

  if (failed) {
    return (
      <div className={box}>
        <div className="error" style={{ whiteSpace: "pre-line" }}>{run.error}</div>
        <div className="setting-actions">
          <button className="linky" onClick={onClose}>Close</button>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={box}>
        <div className="error">{error}</div>
        <div className="setting-actions">
          <button className="linky" onClick={onClose}>Close</button>
        </div>
      </div>
    );
  }

  if (runner.closing) return null;

  if (started && run && run.running) {
    const done = run.done || 0;
    const total = run.total || 0;
    const pct = total ? Math.min(100, Math.round((done / total) * 100)) : 0;
    const downloading = stage === "Downloading";
    return (
      <div className={box}>
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
      <div className={box}>
        <p style={{ margin: 0 }}><strong>Starting...</strong></p>
      </div>
    );
  }

  return (
    <div className={box}>
      <p style={{ margin: "0 0 10px" }}>
        <strong>Update to version {available}?</strong>
      </p>
      <p className="setting-fine" style={{ margin: "0 0 12px" }}>
        You are on version {version}. The download is about {megabytes(size)}.
        The app closes itself and opens again as a new version. Your settings
        remain the same.
      </p>
      <div className="setting-actions">
        <button className="button" onClick={runner.start}>Update now</button>
        <button className="linky" onClick={onClose}>Not now</button>
      </div>
    </div>
  );
}

/**
 * The whole thing in one piece: a run of its own, the step, and the cover.
 * The app holds the run itself and draws the two halves apart; this is the
 * same behaviour for anything that wants it whole.
 */
export default function UpdateStep(props) {
  const runner = useUpdateRun(props.version);
  if (covers(runner)) return <UpdateCover stuck={runner.stuck} />;
  return <UpdateStepView {...props} runner={runner} />;
}

// The cover goes up once the app is closing, unless a failure is showing,
// which always wins. The same order the step has always checked them in.
export function covers(runner) {
  return runner.closing && !(runner.run && runner.run.error) && !runner.error;
}
