import React, { useEffect, useState } from "react";
import { improvementSources, improvementState, saveImprovements,
         readImprovements, writeParagraph } from "../api.js";

/* The Description of Improvements.
 *
 * Two steps. First Mark sees which two documents the job has and presses a
 * button. Then he sees every value the app could prove, edits what he likes,
 * and approves the two paragraphs. Only then does the Word file build.
 *
 * Nothing is read and nothing is spent until he acts. Coming back to a job he
 * has already read shows what he saved; reading again is a button, because a
 * second read costs money and would throw away his edits.
 */

const PROSE = ["GENERAL", "CONCLUSION"];
const isProse = (b) => PROSE.includes(b.name);

export default function ImprovementsScreen({ job, onBack }) {
  const [sources, setSources] = useState(null);
  const [blocks, setBlocks] = useState([]);
  const [read, setRead] = useState(false);
  const [files, setFiles] = useState({ card: "", transcript: "" });
  const [confirm, setConfirm] = useState(null);   // what will be sent
  const [busy, setBusy] = useState("");
  const [writing, setWriting] = useState("");     // which paragraph is being written
  const [fresh, setFresh] = useState("");         // which one just landed
  const [error, setError] = useState(null);
  const [refused, setRefused] = useState(0);

  useEffect(() => {
    improvementSources(job).then(setSources).catch(() =>
      setError("Could not reach the app's server. Close this tab and start the app again."));
    improvementState(job).then((s) => { setBlocks(s.blocks || []); setRead(!!s.read); })
      .catch(() => {});
  }, [job]);

  function keep(next) {
    setBlocks(next);
    saveImprovements(job, { blocks: next, read: true }).catch(() => {});
  }

  async function ask() {
    setBusy("Looking at the two documents..."); setError(null);
    try {
      const r = await readImprovements(job, { ...files, confirmed: false });
      setConfirm(r);
    } catch (e) { setError(e.message); }
    setBusy("");
  }

  async function doRead() {
    setBusy("Reading the assessor card and the transcript..."); setError(null); setConfirm(null);
    try {
      const r = await readImprovements(job, { ...files, confirmed: true });
      setBlocks(shape(r)); setRead(true); setRefused(r.refused || 0);
      saveImprovements(job, { blocks: shape(r), read: true }).catch(() => {});
    } catch (e) { setError(e.message); }
    setBusy("");
  }

  async function makeParagraph(name) {
    const block = blocks.find((b) => b.name === name);
    if (!block) return;
    setWriting(name); setError(null);
    try {
      const facts = (block.fields || []).filter((f) => f.on && f.value).map((f) => f.value);
      const r = await writeParagraph(job, { block: name, facts, notes: block.notes || "" });
      keep(blocks.map((b) => b.name === name
        ? { ...b, draft: r.text, approved: false } : b));
      setFresh(name); setTimeout(() => setFresh(""), 1700);
    } catch (e) { setError(e.message); }
    setWriting("");
  }

  if (error && !sources) return <p className="error">{error}</p>;
  if (!sources) return <p className="muted">Looking at this job...</p>;

  const proseBlocks = blocks.filter((b) => isProse(b) && b.on !== false);
  const waiting = proseBlocks.filter((b) => !b.approved);
  const canBuild = read && proseBlocks.length > 0 && waiting.length === 0;

  return (
    <>
      <div className="title-row">
        <h1>Description of Improvements</h1>
        <div className="title-actions">
          <button className="linky" onClick={onBack}>Back to the job</button>
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      {!read ? (
        <FirstLook sources={sources} files={files} setFiles={setFiles}
                   busy={busy} confirm={confirm} onAsk={ask} onRead={doRead}
                   onCancel={() => setConfirm(null)} />
      ) : (
        <div className="bands">
          <div>
            <div className="band-head">
              <h2>What it found</h2>
              <span className="note">click a tick to see the words it came from</span>
            </div>
            <ReadFrom sources={sources} onAgain={() => { setRead(false); setConfirm(null); }} />
            {refused > 0 && (
              <p className="band-note">
                {refused} {refused === 1 ? "value was" : "values were"} left out because the
                two documents do not say {refused === 1 ? "it" : "them"}.
              </p>
            )}
            {waiting.length > 0 && (
              <p className="gate">
                The Word file waits on {waiting.map((b) => b.name).join(" and ")}.
              </p>
            )}
            {blocks.map((b) => (
              <Block key={b.name + (b.part || "")} block={b} blocks={blocks} keep={keep}
                     writing={writing} onWrite={makeParagraph} />
            ))}
          </div>
          <div>
            <div className="band-head"><h2>What will print</h2></div>
            <Preview blocks={blocks} fresh={fresh} />
            <div className="folder-result">
              <button className="btn" disabled={!canBuild}>Make the Word file</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

/* The server returns one entry per source, so a field both documents support
   comes back twice. They are folded into one row carrying both quotes, because
   two documents agreeing is one fact, not two. */
function shape(r) {
  const out = [];
  const at = (name, part) => {
    let b = out.find((x) => x.name === name && (x.part || "") === (part || ""));
    if (!b) { b = { name, part: part || "", on: true, fields: [], notes: "", draft: "", approved: false }; out.push(b); }
    return b;
  };
  PROSE.forEach((n) => at(n, ""));
  (r.parts || []).forEach(() => {});
  (r.found || []).forEach((f) => {
    const b = at(f.block, f.part);
    let row = b.fields.find((x) => x.label === f.field);
    if (!row) { row = { label: f.field, value: f.value, on: true, card: "", transcript: "", open: "" }; b.fields.push(row); }
    row[f.source === "card" ? "card" : "transcript"] = f.quote;
    if (!row.value) row.value = f.value;
  });
  return out;
}

function ReadFrom({ sources, onAgain }) {
  const card = sources.cards[0], tx = sources.transcripts[0];
  return (
    <div className="read-from">
      <div><span className="what">PRC</span> <span className="file">{card ? card.name : "none"}</span></div>
      <div><span className="what">Transcript</span> <span className="file">{tx ? tx.name : "none"}</span></div>
      <button className="linky" onClick={onAgain}>Read them again</button>
    </div>
  );
}

function FirstLook({ sources, files, setFiles, busy, confirm, onAsk, onRead, onCancel }) {
  const pick = (kind, list) => (
    <div className="have-row">
      <span className="what">{kind === "card" ? "PRC" : "Transcript"}</span>
      {list.length === 0 ? <span className="file">none in this job</span> : (
        <select value={files[kind] || list[0].rel}
                onChange={(e) => setFiles({ ...files, [kind]: e.target.value })}>
          {list.map((f) => <option key={f.rel} value={f.rel}>{f.rel}</option>)}
        </select>
      )}
    </div>
  );
  return (
    <div className="bands">
      <div>
        <div className="band-head"><h2>What this job has</h2></div>
        <div className="have">
          {pick("card", sources.cards)}
          {pick("transcript", sources.transcripts)}
        </div>
        <p className="band-note">
          Comparable sales are never offered here. A comparable's record card
          describes a different building.
        </p>
      </div>
      <div>
        <div className="band-head"><h2>The section</h2></div>
        {!sources.ai_available ? (
          <p className="band-note">
            Reading documents needs a key on this computer. Open Settings to add one.
          </p>
        ) : confirm ? (
          <div className="ready">
            <div>
              <div className="msg">About to send two documents</div>
              <div className="sub">
                {confirm.card} and {confirm.transcript}, {confirm.characters.toLocaleString()} characters.
              </div>
            </div>
            <button className="btn" onClick={onRead}>Send them</button>
            <button className="linky" onClick={onCancel}>Not yet</button>
          </div>
        ) : (
          <div className="ready">
            <div>
              <div className="msg">{sources.ready ? "Ready to make" : "Not ready"}</div>
              <div className="sub">
                {sources.ready
                  ? "Nothing is read until you press the button."
                  : "This section needs both a PRC and an inspection transcript."}
              </div>
            </div>
            <button className="btn" disabled={!sources.ready || !!busy} onClick={onAsk}>
              {busy ? "Working..." : "Read them"}
            </button>
          </div>
        )}
        {busy && <p className="band-note">{busy}</p>}
      </div>
    </div>
  );
}

function Block({ block, blocks, keep, writing, onWrite }) {
  const [shut, setShut] = useState(false);
  const prose = isProse(block);
  const put = (patch) => keep(blocks.map((b) =>
    b === block ? { ...b, ...patch } : b));
  const putField = (i, patch) => put({
    fields: block.fields.map((f, n) => (n === i ? { ...f, ...patch } : f)) });
  const live = (block.fields || []).filter((f) => f.on).length;
  const title = block.part ? `${block.name} – ${block.part}` : block.name;
  const tally = prose
    ? (writing === block.name ? "writing..." : block.approved ? "approved"
       : block.draft ? "waiting on you" : "not written yet")
    : `${live} of ${(block.fields || []).length} on`;

  return (
    <div className={`blk${shut ? " shut" : ""}${block.on === false ? " off" : ""}`}>
      <h3 onClick={() => setShut(!shut)}>
        <span className="caret">{shut ? "▶" : "▼"}</span>
        <input type="checkbox" checked={block.on !== false} onClick={(e) => e.stopPropagation()}
               onChange={(e) => put({ on: e.target.checked })}
               aria-label={`include ${title}`} />
        {title}
        <span className="tally">{block.on === false ? "left out" : tally}</span>
      </h3>
      {!shut && (
        <div className="body">
          <div className="hdr">
            <span /><span>{prose ? "Line" : "Field"}</span><span>Value</span>
            <span className="c">PRC</span><span className="c">Transcript</span>
          </div>
          {(block.fields || []).map((f, i) => (
            <Field key={f.label} field={f} onChange={(patch) => putField(i, patch)} />
          ))}
          {prose && <Paragraph block={block} put={put} writing={writing} onWrite={onWrite} />}
        </div>
      )}
    </div>
  );
}

function Field({ field, onChange }) {
  const gap = !field.card && !field.transcript;
  return (
    <div className={`f${field.on ? "" : " off"}${gap ? " gap" : ""}`}>
      <input type="checkbox" checked={!!field.on}
             onChange={(e) => onChange({ on: e.target.checked })}
             aria-label={`include ${field.label}`} />
      <span className="lab">{field.label}</span>
      <span>
        <input className="val" value={field.value || ""}
               placeholder="Nothing in either document. Type it here."
               onChange={(e) => onChange({ value: e.target.value })} />
        {field.open === "card" && field.card && <span className="q"><b>PRC</b> {field.card}</span>}
        {field.open === "transcript" && field.transcript && <span className="q"><b>TRANSCRIPT</b> {field.transcript}</span>}
      </span>
      <Tick have={field.card} on={field.open === "card"} what="the PRC"
            onClick={() => onChange({ open: field.open === "card" ? "" : "card" })} />
      <Tick have={field.transcript} on={field.open === "transcript"} what="the transcript"
            onClick={() => onChange({ open: field.open === "transcript" ? "" : "transcript" })} />
    </div>
  );
}

function Tick({ have, on, what, onClick }) {
  if (!have) return <span className="mark no">&middot;</span>;
  return (
    <button type="button" className={`mark${on ? " open" : ""}`} onClick={onClick}
            title={`show the words from ${what}`}>&#10003;</button>
  );
}

function Paragraph({ block, put, writing, onWrite }) {
  const busy = writing === block.name;
  const facts = (block.fields || []).filter((f) => f.on && f.value).length;
  return (
    <>
      <p className="facts">
        These are the facts it may use. It reads nothing else, not the PRC and
        not the transcript.
      </p>
      <div className="notes">
        <label htmlFor={`n-${block.name}`}>
          Anything else that belongs in this paragraph? The building's history,
          the year it was renovated, anything the two documents do not carry.
        </label>
        <textarea id={`n-${block.name}`} value={block.notes || ""}
                  placeholder="Type it here and it goes into the draft."
                  onChange={(e) => put({ notes: e.target.value })} />
      </div>
      {!block.draft ? (
        <div className="write">
          <button type="button" className="btn" disabled={busy} onClick={() => onWrite(block.name)}>
            {busy ? "Writing..." : "Write this paragraph"}
          </button>
          <span className="why">
            from {facts} approved {facts === 1 ? "fact" : "facts"}
            {(block.notes || "").trim() ? " and your notes" : ""}
          </span>
        </div>
      ) : (
        <>
          <textarea className="draft" value={block.draft}
                    onChange={(e) => put({ draft: e.target.value, approved: false })} />
          <div className="okrow">
            {block.approved ? (
              <>
                <span className="stamp">&#10003; Approved</span>
                <button type="button" className="linky" onClick={() => put({ approved: false })}>Change it</button>
              </>
            ) : (
              <>
                <button type="button" className="btn" onClick={() => put({ approved: true })}>
                  Approve this paragraph
                </button>
                <button type="button" className="linky" disabled={busy}
                        onClick={() => onWrite(block.name)}>
                  {busy ? "Writing..." : "Write it again"}
                </button>
              </>
            )}
          </div>
        </>
      )}
    </>
  );
}

function Preview({ blocks, fresh }) {
  return (
    <div className="paper">
      <div className="ttl">DESCRIPTION OF IMPROVEMENTS</div>
      {blocks.filter((b) => b.on !== false).map((b) => {
        const title = b.part ? `${b.name} – ${b.part.toUpperCase()}` : b.name;
        if (isProse(b)) {
          return (
            <div key={title}>
              <div className="h">{title}:</div>
              {b.draft
                ? <p className={`${b.approved ? "" : "pending"}${fresh === b.name ? " fresh" : ""}`}>
                    {b.draft}
                    {!b.approved && <span className="await">Not approved yet</span>}
                  </p>
                : <p className="todo">[ not written yet ]</p>}
            </div>
          );
        }
        const live = (b.fields || []).filter((f) => f.on);
        if (!live.length) return null;
        return (
          <div key={title}>
            <div className="h">{title}:</div>
            {live.map((f) => (
              <div className="row" key={f.label}>
                <span className="l">{f.label}:</span>
                <span>{f.value || <span className="todo">[ you write this ]</span>}</span>
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
}
