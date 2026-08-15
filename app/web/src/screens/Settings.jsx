import React, { useEffect, useState } from "react";
import { getSettings, saveKey, removeKey, forgetWorkspace } from "../api.js";

export default function Settings({ workspace, onChangeFolder, onWorkspaceChanged }) {
  const [state, setState] = useState(null);
  const [typed, setTyped] = useState("");
  const [replacing, setReplacing] = useState(false);
  const [busy, setBusy] = useState("");
  const [note, setNote] = useState(null);
  const [error, setError] = useState(null);
  const [forgetting, setForgetting] = useState(false);

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

      <div className="setting">
        <div className="setting-head"><h2>Where your jobs live</h2></div>
        <p className="setting-body">
          The app is pointed at <strong>{workspace.path}</strong>, which holds{" "}
          {workspace.folder_count} {workspace.folder_count === 1 ? "folder" : "folders"}.
        </p>
        {workspace.source === "override" && (
          <p className="setting-fine">
            This is set by RRF_JOBS_HOME on this computer, which overrides the saved choice.
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
              <button className="button" disabled={!!busy} onClick={async () => {
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
            <button className="button" onClick={onChangeFolder}>Change jobs folder</button>
            <button className="linky" onClick={() => { setForgetting(true); setNote(null); }}>
              Start setup over
            </button>
          </div>
        )}
      </div>

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
              <button className="button" onClick={() => { setReplacing(true); setNote(null); }}>
                Replace it
              </button>
              <button className="linky" onClick={onRemove} disabled={!!busy}>Remove it</button>
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
              <button className="button" onClick={onSave} disabled={!typed.trim() || !!busy}>
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

        {note && <div className="done">{note}</div>}
        {error && <div className="error">{error}</div>}

        <p className="setting-fine">
          Your key is kept in a file in your own user folder, outside this program, and it is
          never shown on screen again or written into any job.
        </p>
      </div>
    </>
  );
}
