import React, { useEffect, useState } from "react";
import { getSettings, saveKey, removeKey, forgetWorkspace, checkForUpdate, logRecent, logSend, closeTheApp } from "../api.js";
import CloseX from "../CloseX.jsx";

export default function Settings({ workspace, version, onChangeFolder, onWorkspaceChanged, onUpdateChecked }) {
  const [state, setState] = useState(null);
  const [typed, setTyped] = useState("");
  const [replacing, setReplacing] = useState(false);
  const [busy, setBusy] = useState("");
  const [note, setNote] = useState(null);
  const [error, setError] = useState(null);
  const [forgetting, setForgetting] = useState(false);
  // The look at startup is silent because he did not ask for it. This one
  // answers either way, because he did.
  const [looking, setLooking] = useState(false);
  const [looked, setLooked] = useState(null);
  const [logNote, setLogNote] = useState(null);
  // What the server says would be sent, once she has asked to see it. Never
  // fetched at load: reading the log costs two file reads and she has not
  // asked for it.
  const [log, setLog] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(null);
  const [closing, setClosing] = useState(false);
  // "Things should be hidden more too." Spenser, 2026-09-04. Two
  // paragraphs on this screen are reassurance: where the key file is
  // kept, and what the app writes into its log. He reads both on every
  // visit, forever. They are folded behind a link and the answer is
  // still one click away.
  const [showsKeyHome, setShowsKeyHome] = useState(false);
  const [showsLogWhat, setShowsLogWhat] = useState(false);

  useEffect(() => {
    getSettings().then(setState)
      .catch(() => setError("Could not reach the app's server. Close this tab and start the app again."));
  }, []);

  async function onSave() {
    setBusy("Checking the key..."); setError(null); setNote(null);
    try {
      const r = await saveKey(typed);
      setState(r); setNote(r.message); setTyped(""); setReplacing(false);
    } catch (e) { setError(e.message); }
    setBusy("");
  }

  async function onRemove() {
    setBusy("Removing..."); setError(null); setNote(null);
    try {
      const r = await removeKey();
      setState(r); setNote(r.message);
    } catch (e) { setError(e.message); }
    setBusy("");
  }

  if (error && !state) return (<><h1>Settings</h1><div className="error">{error}</div></>);
  if (!state) return <p className="sub">Loading...</p>;

  const asking = !state.key_set || replacing;

  return (
    <>
      <h1>Settings</h1>
      <p className="sub">Set this up once. The app remembers it on this computer.</p>

      {/* Two columns, which is click 11 of the walk of 2026-09-04 and was
          asked for again on 2026-09-15: *"why does the setting screen still
          look like 5 panesl down instead of 1 | 2 / 3 | 4 / 5 | 6"*. The
          left column carries the card that changes what the app can do and
          the two he comes here to work in. The right column carries the two
          he glances at. Below 900px there is one column, in this order. */}
      <div className="settings-grid">
        <div className="settings-col">
          <div className="setting">
            <div className="setting-head">
              <h2>Writing captions and reading letters</h2>
              <span className={`lamp ${state.key_set ? "on" : "off"}`}>
                {state.key_set ? "On" : "Off"}
              </span>
            </div>

            <p className="setting-body">
              Two things need a key from Anthropic: writing photo captions for you, and reading
              a signed engagement letter to fill in a new job. Everything else in the app works
              the same either way, and you can always type captions in yourself.
            </p>

            {state.key_set && !replacing && (
              <>
                <p className="setting-body">
                  A key is saved on this computer. It ends in <strong>{state.ends_with}</strong>.
                </p>
                <div className="setting-actions">
                  <button className="button secondary" onClick={() => { setReplacing(true); setNote(null); }}>
                    Replace it
                  </button>
                  <button className="button final" onClick={onRemove} disabled={!!busy}>Remove it</button>
                </div>
              </>
            )}

            {asking && (
              <>
                <label className="field" style={{ maxWidth: 520 }}>
                  <span className="key-label">Paste your key</span>
                  <input type="password" value={typed} autoComplete="off" spellCheck="false"
                    placeholder="Paste it here" onChange={(e) => setTyped(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter" && typed.trim()) onSave(); }} />
                </label>
                <div className="setting-actions">
                  <button className="button secondary" onClick={onSave} disabled={!typed.trim() || !!busy}>
                    Check and save
                  </button>
                  {replacing && (
                    <button className="linky" onClick={() => { setReplacing(false); setTyped(""); }}>
                      Cancel
                    </button>
                  )}
                  {busy && (
                    <span className="working">
                      <span className="loading-bar"><span /></span>
                      <span className="working-text">{busy}</span>
                    </span>
                  )}
                </div>
                <p className="setting-body" style={{ marginTop: 16 }}>
                  You get a key from <strong>console.anthropic.com</strong>, under Settings, then
                  Keys. Anthropic calls it an API key on their site. It is a long line of
                  characters starting with <strong>sk-ant-</strong>. Copy the whole thing.
                </p>
              </>
            )}

            {note && (
              <div className="done">
                <CloseX onClose={() => setNote(null)} what="this message" />
                {note}
              </div>
            )}
            {error && (
              <div className="error">
                <CloseX onClose={() => setError(null)} what="this message" />
                {error}
              </div>
            )}

            <div className="setting-actions">
              <button className="linky" aria-expanded={showsKeyHome}
                      onClick={() => setShowsKeyHome(!showsKeyHome)}>
                Where the key is kept
              </button>
            </div>
            {showsKeyHome && (
              <p className="setting-fine">
                It is kept in a file in your own user folder, outside this program, and it is
                never shown on screen again or written into any job.
              </p>
            )}
          </div>
          <div className="setting">
            <div className="setting-head"><h2>Where your jobs live</h2></div>
            <p className="setting-body">
              The app is pointed at <strong>{workspace.path}</strong>, which holds{" "}
              {workspace.folder_count} {workspace.folder_count === 1 ? "folder" : "folders"}.
            </p>
            {workspace.source === "override" && (
              <p className="setting-fine">
                This computer is set to use this folder. Changing it here will not stick.
              </p>
            )}

            {/* The question the action raises is asked inside the action, when he
                clicks it, not parked on the page beside it. */}
            {forgetting ? (
              <>
                <p className="setting-body">
                  Forget this jobs folder? Your jobs will not be changed. The app will ask
                  you to choose the folder again.
                </p>
                <div className="setting-actions">
                  <button className="button final" disabled={!!busy} onClick={async () => {
                    setBusy("Forgetting..."); setError(null);
                    try { onWorkspaceChanged(await forgetWorkspace()); }
                    catch (e) { setError(e.message); setBusy(""); setForgetting(false); }
                  }}>
                    Forget it
                  </button>
                  <button className="linky" onClick={() => setForgetting(false)}>Cancel</button>
                </div>
              </>
            ) : (
              <div className="setting-actions">
                <button className="linky" onClick={onChangeFolder}>Change jobs folder</button>
                <button className="linky" onClick={() => { setForgetting(true); setNote(null); }}>
                  Start setup over
                </button>
              </div>
            )}
          </div>
          <div className="setting">
            <div className="setting-head"><h2>What the app has done</h2></div>
            <div className="setting-actions" style={{ marginBottom: 14 }}>
              <button className="linky" aria-expanded={showsLogWhat}
                      onClick={() => setShowsLogWhat(!showsLogWhat)}>
                What is in it
              </button>
            </div>
            {showsLogWhat && (
              <p className="setting-body">
                The app writes down what it does, in a file on this computer. If a screen ever
                sits without answering, this is what Spenser needs to see. One press sends him
                the last two days of it.
              </p>
            )}

            <div className="setting-actions">
              {/* Filled blue, by the colour law of 2026-09-08. Not filled red:
                  that is for something he cannot take back that also writes into
                  a folder Mark keeps or replaces the program, and the whole app
                  carries three of those. This writes nothing of his anywhere. */}
              <button className="button secondary" disabled={sending} onClick={async () => {
                setSending(true); setSent(null); setLogNote(null);
                try {
                  setSent(await logSend());
                } catch {
                  // The one failure the server cannot word for itself, because
                  // it is the server that is missing. Still not a dead end.
                  setSent({ sent: false, message:
                    "The app's own server did not answer, so nothing was sent. Start the app "
                    + "again from the Roy R. Fisher icon, or press Show what will be sent, "
                    + "press Copy, and paste it into an email to d.spensernelson@gmail.com." });
                }
                setSending(false);
              }}>
                {sending ? "Sending..." : "Send the log to Spenser"}
              </button>
            </div>

            {sent && (
              <p className={sent.sent ? "done" : "error"} style={{ whiteSpace: "pre-line" }}>
                <CloseX onClose={() => setSent(null)} what="this message" />
                {sent.message}
              </p>
            )}

            <div className="setting-actions" style={{ marginTop: 16 }}>
              {/* Blue text, no box. The colour law of 2026-09-08: this shows her
                  something and changes nothing, which is exactly `.linky`. */}
              <button className="linky" disabled={loading} onClick={async () => {
                setLogNote(null); setLoading(true);
                try { setLog(await logRecent()); }
                catch (e) { setLog(null); setLogNote(e.message); }
                setLoading(false);
              }}>
                Show what will be sent
              </button>
              {loading && (
                <span className="working">
                  <span className="loading-bar"><span /></span>
                  <span className="working-text">Reading the log...</span>
                </span>
              )}
            </div>

            {log && log.empty && (
              <p className="setting-body">
                Nothing has been written yet. There is no log on this computer to show
                or to send.
              </p>
            )}

            {log && !log.empty && (
              <>
                <div className="setting-actions">
                  <button className="linky" onClick={async () => {
                    setLogNote(null);
                    try {
                      await navigator.clipboard.writeText(log.text);
                      setLogNote("Copied. You can paste it into an email.");
                    } catch {
                      // Never a dead end. The text is on the screen either way,
                      // so the way through is always to select it by hand.
                      setLogNote("This browser would not copy it. Select the text below "
                                 + "and press Ctrl and C.");
                    }
                  }}>
                    Copy
                  </button>
                  <button className="linky" onClick={() => { setLog(null); setLogNote(null); }}>
                    Hide it
                  </button>
                </div>
                <pre className="logtext">{log.text}</pre>
              </>
            )}

            {logNote && <p className="setting-fine">{logNote}</p>}
          </div>
        </div>
        <div className="settings-col">
          <div className="setting">
            <div className="setting-head"><h2>The version you are running</h2></div>
            <p className="setting-body">
              This computer is running <strong>version {version || "unknown"}</strong>.
            </p>
            <div className="setting-actions">
              <button className="button secondary" disabled={looking} onClick={async () => {
                setLooking(true); setLooked(null);
                try {
                  const found = await checkForUpdate();
                  // The masthead holds its own copy of this answer and only ever
                  // asked once, at load. Without this it goes on saying nothing
                  // while this screen says a newer version is there.
                  if (onUpdateChecked) await onUpdateChecked();
                  setLooked(found.available
                    ? `Version ${found.available} is available. Use the Update available button at the top of the screen.`
                    : "You are on the newest version.");
                } catch {
                  setLooked("The update service could not be reached just now. Nothing has changed.");
                }
                setLooking(false);
              }}>
                Check now
              </button>
              {looking && (
                <span className="working">
                  <span className="loading-bar"><span /></span>
                  <span className="working-text">Checking...</span>
                </span>
              )}
            </div>
            {looked && <p className="setting-fine">{looked}</p>}
          </div>
          <div className="setting">
            <div className="setting-head"><h2>Closing the app</h2></div>
            {closing ? (
              <p className="setting-body">
                <strong>Closing now.</strong> You can close this tab. Start the app
                again with the Roy R. Fisher icon on your Desktop.
              </p>
            ) : (
              <>
                <p className="setting-body">
                  The app keeps running after you close the browser tab. Use this
                  when you have finished for the day.
                </p>
                <div className="setting-actions">
                  <button className="button final" onClick={async () => {
                    setClosing(true);
                    try { await closeTheApp(); } catch { /* it is going away */ }
                  }}>
                    Close the app
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
