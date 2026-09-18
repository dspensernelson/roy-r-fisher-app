import React, { useEffect, useState } from "react";
import { getSettings, saveKey, removeKey, forgetWorkspace, checkForUpdate, logRecent, logSend } from "../api.js";
import CloseX from "../CloseX.jsx";

export default function Settings({ workspace, version, onChangeFolder, onWorkspaceChanged, onUpdateChecked, onUpdate }) {
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
  const [newer, setNewer] = useState(false);
  const [logNote, setLogNote] = useState(null);
  // What the server says would be sent, once she has asked to see it. Never
  // fetched at load: reading the log costs two file reads and she has not
  // asked for it.
  const [log, setLog] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(null);
  // "Things should be hidden more too." Spenser, 2026-09-04. Where the key
  // file is kept is reassurance he reads on every visit, forever, so it is
  // folded behind a link on the button row and the answer is one click away.
  // `What is in it` used to fold the same way on the log card and is gone:
  // Spenser, 2026-09-15, *"what does this actually show?"*. It described the
  // log, and the button beside it shows the log.
  const [showsKeyHome, setShowsKeyHome] = useState(false);

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

  // Folded away, and it reads directly under whichever button row asked for
  // it. Lower right of that row, like every blue link on this screen.
  const keyHome = (
    <button className="linky" aria-expanded={showsKeyHome}
            onClick={() => setShowsKeyHome(!showsKeyHome)}>
      Where the key is kept
    </button>
  );
  const keyHomeSaid = showsKeyHome && (
    <p className="setting-fine">
      It is kept in a file in your own user folder, outside this program, and it is
      never shown on screen again or written into any job.
    </p>
  );

  // The order is his, picked card by card on 2026-09-15 on the approved
  // mockup. An earlier review argued the key card belongs first, because it
  // is the only card that changes what the app can do. He decided otherwise
  // and that is settled. Below 900px there is one column, in this same order.
  const versionCard = (
    <div className="setting">
      <div className="setting-head"><h2>The version you are running</h2></div>
      <p className="setting-body">
        This computer is running <strong>version {version || "unknown"}</strong>.
      </p>
      <div className="setting-actions">
        <button className="button secondary" disabled={looking} onClick={async () => {
          setLooking(true); setLooked(null); setNewer(false);
          try {
            const found = await checkForUpdate();
            // The masthead holds its own copy of this answer and only ever
            // asked once, at load. Without this it goes on saying nothing
            // while this screen says a newer version is there.
            if (onUpdateChecked) await onUpdateChecked();
            setNewer(!!found.available);
            // Three answers, and the words are this screen's own. Nothing the
            // update server sent reaches here, only whether it answered.
            // "Newest" is said only when it did: Spenser, 2026-09-17, after it
            // was said when the server could not be reached at all.
            setLooked(found.available
              ? `Version ${found.available} is available.`
              : found.could_not_check
                ? "Could not check for a new version."
                : "You are on the newest version.");
          } catch {
            setLooked("The update service could not be reached just now. Nothing has changed.");
          }
          setLooking(false);
        }}>
          Check now
        </button>
        {/* Spenser, 2026-09-16: "When Check now finds a version, an Update
            button appears beside it." The masthead's own words and the
            masthead's own handler, so there is one way into the update and
            this is a second door to it, not a second route. A button, not a
            link: it leads to a step. */}
        {newer && onUpdate && (
          <button className="button secondary" onClick={onUpdate}>
            Update available
          </button>
        )}
        {looking && (
          <span className="working">
            <span className="loading-bar"><span /></span>
            <span className="working-text">Checking...</span>
          </span>
        )}
        {/* Spenser, 2026-09-18: "This should be off to the right of the
            button, not below it." Last in the row, so it reads after the
            buttons. The row wraps, so on a narrow screen it falls under. */}
        {looked && <span className="check-answer">{looked}</span>}
      </div>
    </div>
  );

  const jobsCard = (
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
        /* Spenser, 2026-09-15: *"lets make the 'change jobs' and start 'setup
           over' buttons instead of linksl"*. The colour law of 2026-09-08
           decides which is which. Changing the folder does work for him and he
           can point it somewhere else after, so it is filled blue. Starting
           over throws away what he saved and cannot be taken back, but it is
           not why he opened Settings, which is the plain button with red text
           exactly. No red fill: that is for the one thing a screen is for, and
           this screen is not for wiping his setup. */
        <div className="setting-actions">
          <button className="button secondary" onClick={onChangeFolder}>Change jobs folder</button>
          <button className="button final" onClick={() => { setForgetting(true); setNote(null); }}>
            Start setup over
          </button>
        </div>
      )}
    </div>
  );

  const logCard = (
    <div className="setting">
      <div className="setting-head"><h2>What the app has done</h2></div>

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

        {/* A button, and that bends the colour law of 2026-09-08 knowingly.
            By the letter of it, showing the log on screen moves nothing and
            writes nothing, so it is `.linky`. Spenser, 2026-09-15: *"Make
            this a button like Send the log"*. When sending fails this is not
            decoration; it is the only way the log reaches anybody. It is the
            escape hatch, and an escape hatch dressed as small print is a
            fault this app has already paid for. */}
        <button className="button secondary" disabled={loading} onClick={async () => {
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

      {sent && (
        <p className={sent.sent ? "done" : "error"} style={{ whiteSpace: "pre-line" }}>
          <CloseX onClose={() => setSent(null)} what="this message" />
          {sent.message}
        </p>
      )}

      {log && log.empty && (
        <p className="setting-body" style={{ marginTop: 14 }}>
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
  );

  // No sentence under the heading, and nobody is to put one back. What the
  // sentence was for was telling him the key costs money. That is said where
  // the money is actually spent, on the generate window, at the moment he
  // agrees to the figure. Said again here it is the reassurance-on-every-visit
  // that HOW-WE-WORK.md warns about, on a screen he sets up once.
  const keyCard = (
    <div className="setting">
      <div className="setting-head">
        <h2>Your Anthropic key</h2>
        <span className={`lamp ${state.key_set ? "on" : "off"}`}>
          {state.key_set ? "On" : "Off"}
        </span>
      </div>

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
            {keyHome}
          </div>
          {keyHomeSaid}
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
            {busy && (
              <span className="working">
                <span className="loading-bar"><span /></span>
                <span className="working-text">{busy}</span>
              </span>
            )}
            {replacing && (
              <button className="linky" onClick={() => { setReplacing(false); setTyped(""); }}>
                Cancel
              </button>
            )}
            {keyHome}
          </div>
          {keyHomeSaid}
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
    </div>
  );

  return (
    <>
      <h1>Settings</h1>
      <p className="sub">Set this up once. The app remembers it on this computer.</p>

      {/* Two columns, which is click 11 of the walk of 2026-09-04. The order
          inside them is the one he chose on 2026-09-15, card by card, on the
          approved mockup. `Close the app` is not here at all: it is in the
          nav bar now, which is F13. */}
      <div className="settings-grid">
        <div className="settings-col">
          {versionCard}
          {jobsCard}
        </div>
        <div className="settings-col">
          {logCard}
          {keyCard}
        </div>
      </div>
    </>
  );
}
