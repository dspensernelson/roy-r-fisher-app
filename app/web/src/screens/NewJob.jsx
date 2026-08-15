import React, { useEffect, useRef, useState } from "react";
import { proposeName, createIntake } from "../api.js";

const ENGAGEMENTS = ["Full appraisal", "Tax appeal", "Restricted short form", "Rent study", "Right of way"];
const TYPES = ["retail", "office", "industrial", "multi-family", "special purpose"];
const BLANK = {
  street: "", city: "", state: "Iowa", property_type: "", engagement: "",
  client: "", intended_use: "", effective_date: "", due_date: "", file_number: "",
};

export default function NewJob({ onCreated, onCancel }) {
  // Two ways in, then the same form. Picking the road is its own step so the
  // form is not a wall of fields the moment he clicks New job.
  const [road, setRoad] = useState(null);
  const [form, setForm] = useState(BLANK);
  const [name, setName] = useState("");
  const [nameEdited, setNameEdited] = useState(false);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState(null);
  const filePicker = useRef(null);

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  // The folder name follows what he types until the moment he edits it
  // himself, and then it is his.
  useEffect(() => {
    if (nameEdited || !road) return;
    if (!form.city.trim() || !form.street.trim() || !form.engagement) return;
    const year = Number((form.effective_date.match(/\b(20\d\d)\b/) || [])[1]) || undefined;
    proposeName({ city: form.city, street: form.street, engagement: form.engagement, year })
      .then((r) => setName(r.name))
      .catch(() => {});
  }, [form.city, form.street, form.engagement, form.effective_date, nameEdited, road]);

  async function create() {
    setBusy("Making the folders..."); setError(null);
    try {
      const r = await createIntake({ ...form, name });
      onCreated(r.name);
    } catch (e) { setError(e.message); setBusy(""); }
  }

  const ready = form.street.trim() && form.city.trim() && form.property_type
    && form.engagement && name.trim();

  if (!road) {
    return (
      <>
        <h1>New job</h1>
        <p className="sub">Two ways to start. Both end at the same form, and you check every line before anything is made.</p>
        <div className="roads">
          <button className="road" onClick={() => setRoad("type")}>
            <span className="road-title">Type it in</span>
            <span className="road-body">
              The address, what kind of property it is, and what kind of appraisal.
              About a minute.
            </span>
          </button>
          <button className="road" onClick={() => { setRoad("letter"); filePicker.current?.click(); }}>
            <span className="road-title">Read the engagement letter</span>
            <span className="road-body">
              Drop the signed letter and the app fills in what it can find.
              You check it before anything is saved.
            </span>
            <span className="road-soon">Not built yet</span>
          </button>
        </div>
        <div style={{ marginTop: 20 }}>
          <button className="linky" style={{ marginLeft: 0 }} onClick={onCancel}>Cancel</button>
        </div>
      </>
    );
  }

  return (
    <>
      <h1>New job</h1>
      <p className="sub">Nothing is made until you press the button at the bottom.</p>

      {road === "letter" && (
        <div className="warn" style={{ maxWidth: 720 }}>
          Reading a letter is not built yet. Fill this in and everything else works the same.
        </div>
      )}

      <div className="panel">
        <h2>Needed to start</h2>
        <div className="fields">
          <div className="field"><label>Street address</label>
            <input value={form.street} onChange={set("street")} placeholder="4151 4th St SW" autoFocus /></div>
          <div className="field"><label>City</label>
            <input value={form.city} onChange={set("city")} placeholder="Mason City" /></div>
          <div className="field"><label>State</label>
            <input value={form.state} onChange={set("state")} /></div>
          <div className="field"><label>Kind of property</label>
            <select value={form.property_type} onChange={set("property_type")}>
              <option value="">Choose one</option>
              {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select></div>
          <div className="field"><label>Kind of appraisal</label>
            <select value={form.engagement} onChange={set("engagement")}>
              <option value="">Choose one</option>
              {ENGAGEMENTS.map((t) => <option key={t} value={t}>{t}</option>)}
            </select></div>
        </div>
      </div>

      <div className="panel">
        <h2>Can wait</h2>
        <div className="fields">
          <div className="field"><label>Client</label><input value={form.client} onChange={set("client")} /></div>
          <div className="field"><label>Intended use</label><input value={form.intended_use} onChange={set("intended_use")} /></div>
          <div className="field"><label>Effective date of value</label>
            <input value={form.effective_date} onChange={set("effective_date")} placeholder="January 1, 2026" /></div>
          <div className="field"><label>Report due date</label>
            <input value={form.due_date} onChange={set("due_date")} placeholder="June 15, 2026" /></div>
          <div className="field"><label>Office file number</label><input value={form.file_number} onChange={set("file_number")} /></div>
        </div>
        <p className="panel-note">
          The fee is not recorded here. The job points at the engagement letter instead.
        </p>
      </div>

      <div className="panel">
        <h2>Folder name</h2>
        <input className="namebox" value={name}
          onChange={(e) => { setName(e.target.value); setNameEdited(true); }}
          placeholder="Fill in the address and this fills itself in" />
        <p className="panel-note">
          This is the folder that gets made, in your usual style. Edit it if you want it named differently.
        </p>
      </div>

      <div className="screen-actions" style={{ alignItems: "flex-start", marginTop: 4 }}>
        <div className="action-row">
          <button className="button" onClick={create} disabled={!ready || !!busy}>Make the job</button>
          <button className="linky" style={{ marginLeft: 0 }} onClick={onCancel}>Cancel</button>
          {busy && (
            <span className="working">
              <span className="loading-bar"><span /></span>
              <span className="working-text">{busy}</span>
            </span>
          )}
        </div>
      </div>
      {error && <div className="error">{error}</div>}
      <input ref={filePicker} type="file" accept=".pdf,.docx,.txt" style={{ display: "none" }} />
    </>
  );
}
