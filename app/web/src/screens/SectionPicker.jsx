import React, { useEffect, useState } from "react";
import { getSections, putSections } from "../api.js";

export default function SectionPicker({ job, onDone }) {
  const [data, setData] = useState(null);
  const [picked, setPicked] = useState({});
  const [busy, setBusy] = useState("");
  const [error, setError] = useState(null);

  useEffect(() => {
    getSections(job)
      .then((d) => {
        setData(d);
        setPicked(Object.fromEntries(d.sections.map((s) => [s.name, s.chosen])));
      })
      .catch(() => setError("Could not reach the app's server. Close this tab and start the app again."));
  }, [job]);

  async function save() {
    setBusy("Saving..."); setError(null);
    try {
      await putSections(job, data.sections.filter((s) => picked[s.name]).map((s) => s.name));
      onDone();
    } catch (e) { setError(e.message); setBusy(""); }
  }

  if (error) return (<><h1>Sections in this report</h1><div className="error">{error}</div></>);
  if (!data) return <p className="sub">Loading...</p>;

  if (!data.engagement) {
    return (
      <>
        <h1>Sections in this report</h1>
        <div className="error">
          This job does not say what kind of appraisal it is yet, so there is nothing to
          suggest. Add the engagement type to the job brief and come back.
        </div>
      </>
    );
  }

  const count = Object.values(picked).filter(Boolean).length;

  return (
    <>
      <h1>Sections in this report</h1>
      <p className="sub">
        A {data.engagement.toLowerCase()} usually runs these. Uncheck anything this one does not need.
      </p>

      {data.thin_evidence && (
        <div className="warn">
          We have only one finished report of this kind on file, so this list is a starting
          point rather than the firm's standard. Check it carefully.
        </div>
      )}

      <div className="panel">
        <div className="checklist">
          {data.sections.map((s) => (
            <label className={`check ${picked[s.name] ? "" : "off"}`} key={s.name}>
              <input type="checkbox" checked={!!picked[s.name]}
                onChange={(e) => setPicked({ ...picked, [s.name]: e.target.checked })} />
              {s.name}
            </label>
          ))}
        </div>
      </div>

      <div style={{ display: "flex", gap: 14, alignItems: "center" }}>
        <button className="button" onClick={save} disabled={!!busy}>Save these sections</button>
        <span className="sub" style={{ margin: 0 }}>
          {busy || `${count} ${count === 1 ? "section" : "sections"} checked`}
        </span>
      </div>
    </>
  );
}
