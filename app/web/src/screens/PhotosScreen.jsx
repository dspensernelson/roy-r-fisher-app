import React, { useEffect, useRef, useState } from "react";
import CloseX from "../CloseX.jsx";
import { showMoney } from "../money.js";
import { getManifest, putManifest, uploadPhotos, draftCaptions, build, thumbUrl, captionStyles, clearCaptions, cutPhoto, uncutPhoto,
         captionEstimate, captionProgress, captionSamples, markReviewed, markUnreviewed, markAllReviewed, setPhotoBand, putBands, jobFacts, putJobFacts, reveal,
         photoGroups, putPhotoGroup, readingProgress, captionBack, captionsBack, refreshCaption } from "../api.js";

// A size on this screen, in the stylesheet's terms: the design number times
// `--k`, which the photographs frame sets to 0.9. For the few inline styles;
// everything else is in brand.css. See `.frame.is-photos` there.
const k = (n) => `calc(${n}px * var(--k, 1))`;

// The mark on Back, on the tile and in the widget's bar. One drawing at two
// sizes, so the two read as one idea. Drawn in the language of the app's only
// other icon, the photograph with a plus below: thin strokes in currentColor,
// round caps.
function BackMark() {
  return (
    <svg viewBox="0 0 14 13" fill="none" aria-hidden="true">
      <path d="M1.8 4.8H9.0a3 3 0 0 1 0 6H7.4" stroke="currentColor"
            strokeWidth="1.3" strokeLinecap="round" />
      <path d="M4.6 2.0 1.8 4.8l2.8 2.8" stroke="currentColor"
            strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// The mark on refresh. The same hand as Back.
function RefreshMark() {
  return (
    <svg viewBox="0 0 14 14" fill="none" aria-hidden="true">
      <path d="M10.25 3.75A4.6 4.6 0 1 1 7 2.4" stroke="currentColor"
            strokeWidth="1.3" strokeLinecap="round" />
      <path d="M5.5 1.1 7.6 2.4 5.5 3.7" stroke="currentColor"
            strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// One page of the caption chooser's preview, in the shape the engine builds.
// Three-up pairs each photograph with the caption beside it. Six-up puts two
// photographs in a row and their two captions in the row beneath, which is
// the reading order Spenser chose on 2026-09-07.
//
// It draws one of two things and never a mixture of them. `shots` is his own
// photographs with captions actually written from them, which is what the
// money in this window buys. Without it the rows are written specimens of a
// style beside a blank frame: a specimen says nothing about any photograph,
// so it must never sit next to one, or it reads as a caption of it.
function previewRows(samples, perPage, shots) {
  const cells = shots
    ? shots.map((s) => ({ caption: s.caption, src: s.src }))
    : samples.map((line) => ({ caption: line, src: null }));

  const photoCell = (cell, key) => (cell.src
    ? (<div className="cell-photo" key={key}>
         <img src={cell.src} alt="" draggable={false} />
       </div>)
    : <div className="cell-photo is-example" key={key} aria-hidden="true" />);

  if (perPage !== 6) {
    return cells.map((cell, n) => (
      <React.Fragment key={`three-${n}`}>
        {photoCell(cell, `p${n}`)}
        <div className="cell-caption">{cell.caption}</div>
      </React.Fragment>
    ));
  }
  const rows = [];
  for (let i = 0; i < cells.length; i += 2) {
    const pair = cells.slice(i, i + 2);
    rows.push(
      <React.Fragment key={`six-${i}`}>
        {pair.map((cell, n) => photoCell(cell, `p${n}`))}
        {pair.map((cell, n) => (
          <div key={`c${n}`} className="cell-caption">{cell.caption}</div>
        ))}
      </React.Fragment>
    );
  }
  return rows;
}

// Grey, and the shape of the answer, when the app cannot work the name out.
// Spenser's theory, approved 2026-09-14: a screen that makes a file is named
// by that file.
const NO_NAME = "file name here.docx";

export default function PhotosScreen({ job }) {
  const [manifest, setManifest] = useState(null);
  const [styles, setStyles] = useState([]);
  const [asking, setAsking] = useState(false);   // the one captioning window
  const [showing, setShowing] = useState(null);  // which style the examples are toggled to
  // His own photographs captioned in both styles, once he has pressed for
  // them. Money bought these, so they are kept for as long as he is on this
  // job: closing the window and opening it again must never buy them twice.
  const [shots, setShots] = useState(null);
  const [shotsBusy, setShotsBusy] = useState(false);
  const [shotsError, setShotsError] = useState("");
  const [busy, setBusy] = useState("");
  const [done, setDone] = useState(null);
  const [error, setError] = useState(null);
  // How far the photo list has got, while we wait for it. A wait that says
  // nothing looks exactly like a dead screen, and on a network drive this
  // wait is the whole of the screen's first paint.
  const [reading, setReading] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [clearing, setClearing] = useState(false);  // the clear-captions step
  const [showCut, setShowCut] = useState(false);    // the Cut photos section
  const [markingAll, setMarkingAll] = useState(false);
  const [cutNote, setCutNote] = useState("");
  const [aiOn, setAiOn] = useState(true);   // until the app says otherwise
  const [quote, setQuote] = useState(null);   // what a run would send and cost
  const [spent, setSpent] = useState(null);   // what the last run did cost
  // Whether the run's own account of itself is a window over the screen. A run
  // that saved everything and reported a cost is a fact, so it goes on the
  // quiet line. A run that saved some and not others, or failed, or could not
  // say what it cost, is a decision, so it stops him.
  const [spentOpen, setSpentOpen] = useState(false);
  const [facts, setFacts] = useState(null);   // city and address for the filename
  const [fixing, setFixing] = useState(false);
  const [running, setRunning] = useState(null);   // which request the run is on
  const [where, setWhere] = useState(null);   // which folder holds the report photographs
  const [asked, setAsked] = useState(false);  // he re-opened the question himself
  // Which of the quiet line's messages he is looking at. One line shows one
  // thing; the rest are a click away, and never a second box.
  const [at, setAt] = useState(0);
  // The band whose photographs are the only ones showing, or null for all of
  // them. The screen's own business: never sent, never saved, and it never
  // changes the report's order. Spenser, 2026-09-17.
  const [onlyBand, setOnlyBand] = useState(null);
  // Photographs he moved out of the band being shown, kept in view until the
  // filter changes or clears, so one does not vanish from under his pointer
  // the moment he clicks its new letter. Spenser, 2026-09-18. Screen only,
  // like the filter itself.
  const [stayed, setStayed] = useState([]);
  function showBand(letter) { setOnlyBand(letter); setStayed([]); }
  // What he is typing right now, by file name, before it is saved. It is
  // deliberately not in the manifest. Everything that watches the manifest
  // reacts to every change of it, including the price question, which opens
  // photograph files across the office network. A caption he has not finished
  // is not yet a fact about the job, so it waits here until he leaves the box.
  const [typing, setTyping] = useState({});
  // What a photograph is saying about itself, by file name: that its caption
  // is being refreshed, or why the refresh failed. Said on the photograph and
  // nowhere else.
  const [said, setSaid] = useState({});
  // The caption save that is still in the air, if there is one. `Mark
  // reviewed` reads the job's list on the server and answers with what it
  // read, so a caption sent a moment before and still travelling comes back
  // as the old one, and the old one lands on his screen. B13.
  const saving = useRef(Promise.resolve());
  // Whether this job's samples have been bought. Opening the style window
  // buys them; opening it a second time must not buy them again.
  const bought = useRef(false);
  const dragFrom = useRef(null);
  const filePicker = useRef(null);

  useEffect(() => {
    setManifest(null); setError(null); setReading(null);
    // A different job's photographs, so what was bought for the last one is
    // not his any more.
    setShots(null); setShotsError(""); bought.current = false;
    setSaid({}); setStayed([]);
    // Polls alongside the call rather than after it. Nothing was watching at
    // mount, which is exactly when the waiting happens.
    let alive = true;
    const watching = setInterval(() => {
      readingProgress(job).then((at) => { if (alive && at.reading) setReading(at); }).catch(() => {});
    }, 700);
    getManifest(job)
      .then((m) => { if (alive) setManifest(m); })
      .catch((e) => { if (alive) setError(e.message); })
      .finally(() => { alive = false; clearInterval(watching); setReading(null); });
    return () => { alive = false; clearInterval(watching); };
  }, [job]);
  useEffect(() => { jobFacts(job).then(setFacts).catch(() => {}); }, [job]);
  // Where this job keeps its photographs. His office stores every shoot twice,
  // full size and shrunk by hand, under a folder name that changes job to job,
  // so the app asks him once which one is the report rather than guessing.
  useEffect(() => { setAsked(false); photoGroups(job).then(setWhere).catch(() => {}); }, [job]);

  async function onPickFolder(folder) {
    setError(null);
    try {
      await putPhotoGroup(job, folder);
      setAsked(false);
      setWhere(await photoGroups(job));
      setManifest(await getManifest(job));
    } catch (e) { setError(e.message); }
  }

  // The price a run would cost. It is an approximate number and it is only
  // ever read in two places: the count on the button, and the step that spends
  // the money. So it is asked for in two places and nowhere else.
  //
  // It used to be asked for every time the manifest changed, and twelve things
  // change the manifest. Working it out means counting photographs without
  // captions on the server, and counting them opens photograph files. Mark's
  // jobs sit on the office network disk, so each of those was a trip across
  // the network for a number that had not moved. Spenser, 2026-09-14.
  const refreshQuote = React.useCallback(() => {
    captionEstimate(job).then(setQuote).catch(() => {});
  }, [job]);
  useEffect(() => { refreshQuote(); }, [refreshQuote]);
  useEffect(() => {
    captionStyles()
      .then((r) => { setStyles(r.styles); setAiOn(r.ai_available); })
      .catch(() => {});
  }, []);

  // Escape closes the window, the way every dialog on his computer already
  // does. One window at a time, so one key closes whichever is open.
  useEffect(() => {
    const open = asking || markingAll || clearing || fixing || spentOpen;
    if (!open) return;
    const onKey = (e) => {
      if (e.key !== "Escape") return;
      setAsking(false); setMarkingAll(false); setClearing(false);
      setFixing(false); setSpentOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [asking, markingAll, clearing, fixing, spentOpen]);

  async function save(next) {
    setManifest(next);
    return putManifest(job, next).catch((e) => { setError(e.message); return null; });
  }

  // Who wrote a caption he has just finished, and whether it is ticked, as
  // the server decided them. Spenser, 2026-09-18: a caption he types counts
  // as reviewed. That rule lives on the server (`record_typed_captions`), and
  // the screen takes its answer rather than holding a second copy of it.
  // Only if the words are still the ones that were sent: if he has changed
  // them again since, the next save will bring the next answer.
  function adoptWriter(file, answer) {
    const saved = answer && answer.manifest && Array.isArray(answer.manifest.photos)
      ? answer.manifest.photos.find((e) => e.file === file) : null;
    if (!saved) return;
    setManifest((now) => {
      if (!now) return now;
      const photos = now.photos.map((p) => (p.file === file && p.caption === saved.caption
        ? { ...p, author: saved.author, reviewed: saved.reviewed } : p));
      return { ...now, photos };
    });
  }

  async function onFiles(files) {
    if (!files?.length) return;
    setBusy("Copying photos into the job folder..."); setError(null);
    try { setManifest(await uploadPhotos(job, files)); } catch (e) { setError(e.message); }
    setBusy("");
  }

  // Opens the one window, and writes captions from his first three photographs
  // while he looks at it. Spenser authorised that money on 2026-09-04:
  // *"we're going to spend the 3 pennies to generate the 6 suggestions."*
  // It sat behind a button quoting him the price for one evening and he threw
  // the button out on 2026-09-14: he had already agreed, and being asked
  // again is a question with one sensible answer.
  function openChooser() {
    // The second and last place the price is asked for. He is about to be
    // shown a figure and asked to agree to it, so it is worked out again here
    // against whatever is in the job now.
    refreshQuote();
    setShowing(manifest.caption_style || "view");
    setAsking(true);
    askForSamples();
  }

  // Three photographs in both styles, once for this job. Fixed and tiny, and
  // part of opening the window rather than a thing he decides. The ref is the
  // whole of the guard: closing the window and opening it again is free, and
  // so is every redraw. What it really cost is recorded on the server the
  // same way a run is.
  async function askForSamples() {
    if (bought.current || !aiOn) return;
    bought.current = true;
    setShotsBusy(true); setShotsError("");
    try {
      const got = await captionSamples(job);
      if (!got.ai_available || !Object.keys(got.samples || {}).length) {
        setShotsError("Captions could not be written for these photographs. "
                      + "The written examples are below.");
      } else {
        setShots(got);
      }
    } catch (e) { setShotsError(e.message); }
    setShotsBusy(false);
    // The price is not asked again here. Samples write nothing into the job,
    // so the number has not moved, and asking opens photograph files across
    // the office network for an answer that is already on screen.
  }

  // One window, so the button on it is the agreement. It carries the figure,
  // the style and the go-ahead together, and nothing opens on top of it.
  // Spenser, 2026-09-14: *"I want one screen"*. The second window that used to
  // open over this one, quoting the same money a second time, is gone.
  function beginCaptions(style) {
    setAsking(false);
    runCaptions(style, true);
  }

  async function runCaptions(style, confirmed) {
    setAsking(false);
    setBusy("Writing captions..."); setError(null);
    setSpent(null); setSpentOpen(false); setAt(0);
    setRunning({ request: 0, requests: tranches, captioned: 0, total: toSend });

    // While the run is in flight, ask where it has got to and pull down the
    // captions already saved. Each request is written to disk before the next
    // one is sent, so finished work can be on screen rather than waiting for
    // the whole run to come back.
    const watching = setInterval(async () => {
      try {
        const at = await captionProgress(job);
        if (!at.running) return;
        setRunning(at);
        if (at.captioned > 0) setManifest(await getManifest(job));
      } catch { /* a missed tick is not worth a message */ }
    }, 1200);

    try {
      if (style && style !== manifest.caption_style) {
        await save({ ...manifest, caption_style: style });
      }
      const m = await draftCaptions(job, confirmed || needsConfirm);
      setManifest(m);
      // What it actually cost, kept next to what was estimated, and what
      // became of the run, which only the run can say.
      if (m.measured) {
        const account = { ...m.measured, captioned: m.captioned,
                          remaining: m.remaining || [],
                          state: m.state, summary: m.summary };
        setSpent(account);
        // A clean run is a fact and goes on the quiet line. Anything else is
        // a decision and stops him.
        setSpentOpen(!isClean(account));
      }
      // A run that saved something is not an error, whatever one request did.
      if (m.error && m.state === "failed") setError(m.error);
      if (!m.ai_available) {
        setError("Writing captions needs a key on this computer. You can still type them in yourself.");
      }
    } catch (e) { setError(e.message); }
    clearInterval(watching);
    setRunning(null);
    setBusy("");
    refreshQuote();
  }

  // Every caption saved, and the provider said what it cost.
  function isClean(account) {
    if (!account) return true;
    if (account.state === "partial" || account.state === "failed") return false;
    if (account.remaining && account.remaining.length > 0) return false;
    return account.calculated_cost !== null && account.calculated_cost !== undefined;
  }

  async function onReview(file, already) {
    setError(null);
    try {
      // Leaving the box saved the caption. That save has to reach the server
      // before the tick does, or the tick is answered out of the caption the
      // server still holds and throws away what he just typed.
      await saving.current;
      setManifest(already ? await markUnreviewed(job, file) : await markReviewed(job, file));
    } catch (e) { setError(e.message); }
  }

  // The switch, and later the list behind it. Whatever comes back is what the
  // screen draws: it never sorts or seeds anything itself, because the server
  // is the one that decides what a band list looks like.
  async function onBands(body) {
    setError(null);
    try { setManifest(await putBands(job, body)); }
    catch (e) { setError(e.message); }
  }

  // Three or six to a page. It goes through the manifest rather than a route
  // of its own, because it is one value on the job the way caption_style is,
  // and putManifest already refuses anything that is not 3 or 6.
  //
  // The manifest we hold is sent back amended rather than re-fetched first,
  // so this cannot race a caption he is in the middle of typing.
  async function onPerPage(n) {
    if (n === perPage) return;              // pressing the one already on does nothing
    setError(null);
    const next = { ...manifest, photos_per_page: n };
    setManifest(next);                      // the value moves under his finger
    try { await putManifest(job, next); }
    catch (e) { setManifest(manifest); setError(e.message); }
  }

  // One click, one photograph, one band. Clicking the band it is already in
  // takes it back out, so the same click is never a trap.
  async function onBand(file, letter) {
    setError(null);
    if (onlyBand) setStayed((now) => (now.includes(file) ? now : [...now, file]));
    try { setManifest(await setPhotoBand(job, file, letter)); }
    catch (e) { setError(e.message); }
  }

  // One request instead of one per photograph. The warning in front of it is
  // not decoration: it is the only thing standing between a shortcut and
  // nobody having read what the model wrote.
  async function onMarkAll() {
    setMarkingAll(false); setError(null);
    try { setManifest(await markAllReviewed(job)); }
    catch (e) { setError(e.message); }
  }

  async function onFixFacts(city, address) {
    try { setFacts(await putJobFacts(job, { city, address })); setFixing(false); }
    catch (e) { setError(e.message); }
  }

  async function onCut(file) {
    setError(null); setDone(null); setAt(0);
    try {
      setManifest(await cutPhoto(job, file));
      setCutNote("Taken out. The original file was not changed.");
    } catch (e) { setError(e.message); }
  }

  async function onBringBack(file) {
    setError(null); setDone(null); setCutNote("");
    try { setManifest(await uncutPhoto(job, file)); }
    catch (e) { setError(e.message); }
  }

  async function onClearCaptions() {
    setClearing(false);
    setBusy("Clearing captions..."); setError(null); setDone(null); setAt(0);
    try {
      const m = await clearCaptions(job);
      setManifest(m);
      setDone(`${m.cleared} ${m.cleared === 1 ? "caption was" : "captions were"} cleared. `
              + "The photos, their order and the caption style are unchanged.");
    } catch (e) { setError(e.message); }
    setBusy("");
  }

  // Back, on one photograph. It works on its own: it does not wait for the
  // job-wide one and it does not care what any other photograph holds. The
  // tick does not come back with the words, and the server is what makes that
  // true, so the screen simply draws what it is handed.
  async function onCaptionBack(file) {
    setError(null);
    try {
      // The same wait `Mark reviewed` takes, for the same reason. A caption
      // he typed a moment ago may still be travelling, and the server would
      // answer this out of the list it still holds.
      await saving.current;
      setManifest(await captionBack(job, file));
    } catch (e) { setError(e.message); }
  }

  // The job-wide one, in the bar. It spares what he changed: only the
  // photographs still empty since the clear come back. Safe to press twice.
  async function onCaptionsBack() {
    setError(null); setDone(null); setAt(0);
    try {
      await saving.current;
      setManifest(await captionsBack(job));
    } catch (e) { setError(e.message); }
    // A whole job's worth of captions has just changed, so the count on
    // Generate captions and the figure in the bar have both moved. One
    // question, after one press of one button. Deliberately not done by Back
    // on a tile: he can press that sixty times, and working the price out
    // opens photograph files across the office network each time.
    refreshQuote();
  }

  // Refresh, on one photograph. One model call, and it spends the figure
  // printed inside the control, so pressing it is the agreement and no window
  // opens in front of it. The server keeps the words it replaces as this
  // photograph's spare, so Back on the tile undoes it. Spenser, 2026-09-18.
  //
  // While it works, the photograph itself says "Refreshing caption", his
  // words, and a failure is said on that photograph too, never on the line
  // under the title. Spenser, 2026-09-18.
  async function onRefreshCaption(file) {
    setError(null); setDone(null); setAt(0);
    setBusy("Writing captions...");
    setSaid((now) => ({ ...now, [file]: { working: true } }));
    let outcome = null;
    try {
      await saving.current;
      const m = await refreshCaption(job, file);
      setManifest(m);
      if (m && m.written === false) {
        outcome = { failed: "No caption was written. Nothing was changed." };
      }
    } catch (e) { outcome = { failed: e.message }; }
    setSaid((now) => {
      const rest = { ...now };
      if (outcome) rest[file] = outcome; else delete rest[file];
      return rest;
    });
    setBusy("");
    // What the job has spent has moved, so the figure in the bar is asked for
    // again. Once, here, after the money was spent. Never on a redraw.
    refreshQuote();
  }

  async function onBuild() {
    setBusy("Building photo pages..."); setError(null); setDone(null); setAt(0);
    try { setDone(await build(job)); } catch (e) { setError(e.message); }
    setBusy("");
  }

  // Pressed, never automatic. A failure here is not a failed build: the file
  // is already written, so the message says where it is and says so.
  async function onReveal(what) {
    setError(null);
    try { await reveal(job, done.created, what); } catch (e) { setError(e.message); }
  }

  function setCaption(i, caption) {
    const file = manifest.photos[i].file;
    setTyping((held) => ({ ...held, [file]: caption }));
  }

  // He left the box. Only now does what he typed become part of the job, and
  // only now does anything that watches the manifest hear about it.
  function commitCaption(i) {
    const file = manifest.photos[i].file;
    if (!(file in typing)) return;          // he typed nothing in this one
    const caption = typing[file];
    setTyping((held) => {
      const rest = { ...held };
      delete rest[file];
      return rest;
    });
    if (caption === manifest.photos[i].caption) return;   // nothing changed
    const next = structuredClone(manifest);
    next.photos[i].caption = caption;
    saving.current = save(next).then((answer) => adoptWriter(file, answer));
  }

  function drop(i) {
    const from = dragFrom.current;
    if (from === null || from === i) return;
    const next = structuredClone(manifest);
    // The included photos are shuffled between the slots they already
    // occupy. A cut photo keeps its exact index, so bringing it back always
    // returns it to the same place, however much reordering happened while
    // it was out.
    const slots = next.photos.map((p, n) => (p.cut ? -1 : n)).filter((n) => n >= 0);
    const items = slots.map((n) => next.photos[n]);
    const fromPos = slots.indexOf(from);
    const toPos = slots.indexOf(i);
    if (fromPos < 0 || toPos < 0) return;
    const [moved] = items.splice(fromPos, 1);
    items.splice(toPos, 0, moved);
    slots.forEach((slot, k) => { next.photos[slot] = items[k]; });
    dragFrom.current = null;
    save(next);
  }

  // The error comes first, and that ordering is the whole fix. It used to sit
  // below this line, so a photo list that could not be read was caught,
  // stored, and never shown: the screen sat on `Loading...` holding the
  // explanation. Colleen lost a morning to that on 2026-09-03 and the only
  // way out was deleting photo-manifest.json by hand.
  if (!manifest && error) return (
    <>
      <h1>Photos</h1>
      <div className="error">{error}</div>
      <p className="sub">
        Nothing has been changed. Send this to Spenser with the log from Settings.
      </p>
    </>
  );
  if (!manifest) return (
    <p className="sub">
      {reading && reading.total
        ? `Reading photograph ${reading.done} of ${reading.total}...`
        : "Loading..."}
    </p>
  );

  // The question, asked once, when this job keeps its photographs in more than
  // one place and he has not said which is the report. It is here rather than
  // on the job screen because this is the action it shapes: he clicked Open on
  // Subject Photographs, and this is what that needs an answer to.
  //
  // Nothing is guessed from a folder name. Eleven of Mark's jobs use nine
  // different namings and his new helper has just added a tenth, so the app
  // shows him the folders his own office made and he says which.
  //
  // It keeps the word Photos as its title, because no document is in view yet:
  // which photographs the report is made of is exactly what is being asked.
  const needsFolder = !!where && (where.needs_choice || where.chosen_missing || asked);
  if (needsFolder) {
    return (
      <div>
        <div className="screen-head is-asking">
          <div>
            <h1 style={{ margin: 0 }}>Photos</h1>
            <p className="sub" style={{ margin: `${k(4)} 0 0` }}>
              This job keeps photographs in more than one place.
            </p>
          </div>
        </div>

        {where.chosen_missing && (
          <div className="error" style={{ marginTop: 0, marginBottom: k(16) }}>
            The folder you chose, <strong>{where.chosen}</strong>, is not in this
            job any more. Nothing has been built from a different folder. Choose
            again below.
          </div>
        )}

        <div className="confirm" style={{ marginTop: 0 }}>
          <p style={{ margin: `0 0 ${k(4)}` }}>
            <strong>Which folder holds the photographs for this report?</strong>
          </p>
          <p className="setting-fine" style={{ margin: `0 0 ${k(14)}` }}>
            Every photograph stays where it is. This only says which ones go in
            the report, and you can change it later.
          </p>

          <div className="folder-choices">
            {where.groups.map((g) => (
              <button key={g.folder || "(top)"} className="folder-choice"
                      onClick={() => onPickFolder(g.folder)}>
                <img src={thumbUrl(job, g.sample)} alt="" draggable={false} />
                <span className="folder-choice-name">
                  {g.folder || "The Photos folder itself"}
                </span>
                <span className="folder-choice-count">
                  {g.count} {g.count === 1 ? "photograph" : "photographs"}
                </span>
              </button>
            ))}
          </div>

          {asked && !where.chosen_missing && (
            <div className="setting-actions" style={{ marginTop: k(14) }}>
              <button className="linky" onClick={() => setAsked(false)}>Cancel</button>
            </div>
          )}
        </div>
        {error && (
          <div className="error" style={{ marginTop: k(16) }}>
            <CloseX onClose={() => setError(null)} what="this message" />
            {error}
          </div>
        )}
      </div>
    );
  }

  const count = manifest.photos.length;
  // Only captions with something in them can be cleared, so this is the
  // number the confirmation quotes and the number the server will act on.
  // Every caption in the job, taken out or not, because clearing blanks them
  // all. It is not the written count: that one is below, and counts only
  // what is still in the report.
  const captioned = manifest.photos.filter((p) => (p.caption || "").trim()).length;
  // A cut photo keeps its place in the array. These two views are only ever
  // filters of that one list, so nothing is reordered by cutting.
  const inPhotos = manifest.photos.map((p, i) => ({ p, i })).filter((x) => !x.p.cut);
  const cutPhotos = manifest.photos.map((p, i) => ({ p, i })).filter((x) => x.p.cut);
  // How many photographs share a page. The server normalises this on the way
  // out of the manifest route, so it is 3 or 6 and never absent. The `|| 3` is
  // a guard for a manifest that never came from the server, not a second copy
  // of the default rule: the rule lives in `photos_per_page()` in
  // app/server/photos.py, and the engine's Layout is where the shape lives.
  const perPage = manifest.photos_per_page || 3;
  // Exact, not "about". Sixty photographs at three to a page is twenty pages,
  // and the app knows the layout, so it says twenty. Spenser's rule,
  // 2026-09-14: a number the app knows exactly is stated exactly.
  const pagesIn = Math.max(1, Math.ceil(inPhotos.length / perPage));

  // Review, counted from the manifest so the screen and the server agree even
  // if one of them is a moment stale.
  const reviewedCount = inPhotos.filter((x) => x.p.reviewed).length;
  const allReviewed = inPhotos.length > 0 && reviewedCount === inPhotos.length;

  // Written and reviewed are two facts and they are both read from here, so
  // the bar and anything else on the screen cannot disagree about them. They
  // were unrelated state once, which is how the left of the screen said
  // "9 of 12 reviewed" while the box said everything was done. 2026-09-16.
  const allWritten = inPhotos.length > 0
                     && inPhotos.every((x) => (x.p.caption || "").trim());
  // The bar's "N of M reviewed". M is every photograph in the report,
  // captioned or not; N is those whose caption he has read, and a caption he
  // typed counts as read (the server decides that, `record_typed_captions`).
  // Spenser chose this on 2026-09-18, from 0.7.6.3. M used to be the
  // captioned photographs only, so the pill said "✓ 5 of 5 reviewed" with
  // seventeen that had no words, and after he typed one caption it thought
  // there was one to review. docs/CHECKS.md, Check 40, says the same.
  const barOf = inPhotos.length;
  const barRead = inPhotos.filter((x) => x.p.reviewed && (x.p.caption || "").trim()).length;
  // Done, and the only state that carries the tick: every photograph in the
  // report has words and every one has been read.
  const barDone = barOf > 0 && barRead === barOf;

  // What it costs, in the smallest true form. An estimate until money has
  // actually been spent, and then what was spent. Cents while it is pennies,
  // because "about 6 cents" reads as a number and "$0.06" reads as a form.
  const spentTotal = spent && spent.calculated_cost !== null
                     && spent.calculated_cost !== undefined
                     ? spent.calculated_cost : null;
  const estimate = quote && quote.estimate ? quote.estimate.total : null;
  const money = (function () {
    const n = captioned > 0 && spentTotal !== null ? spentTotal : estimate;
    if (n === null || n === undefined) return null;
    // One rule for every figure on this screen, in app/web/src/money.js:
    // whole dollars, rounded up, from $10.
    return showMoney(n, { cents: true });
  }());

  // What one photograph costs, printed inside the refresh control on every
  // tile. It is read off the estimate the screen already asks for, which is
  // asked for when the screen opens, after a run and when the spending window
  // opens, and at no other time. It is deliberately NOT a question per tile
  // and NOT a question per keystroke: this app already shipped a fault where
  // the price was asked for on every letter he typed, one trip across the
  // office network each. Sixty tiles read one number.
  //
  // The same shape as the money in the bar, so a penny reads as a penny.
  const onePhoto = quote && quote.one_photo ? quote.one_photo.total : null;
  const onePhotoPrice = showMoney(onePhoto, { cents: true });
  const onePhotoCents = onePhoto === null || onePhoto === undefined ? null
    : Math.round(onePhoto * 100);

  // The job-wide back is live exactly when it has something to do: a
  // photograph that a clear emptied and that is still empty. Spenser's rule,
  // 2026-09-17: it spares what he changed. So the moment the only copies left
  // belong to photographs he has since typed or refreshed, this has nothing
  // to act on and says so by going grey. Their own Back on the tile still
  // works, which is the whole point of it working on its own.
  const canPutBackAll = manifest.photos.some(
    (p) => (p.cleared_caption || "").trim() && !(p.caption || "").trim());

  // Everything the server told us about this run, read before anything that
  // depends on it. Declared out of order once and the whole screen went blank
  // on a temporal-dead-zone error, which no test caught because none of them
  // render React.
  const toSend = quote ? quote.photos_to_send : inPhotos.filter((x) => !(x.p.caption || "").trim()).length;
  const ceiling = quote ? quote.tranche_size : 60;
  const tranches = quote ? quote.tranches : 1;
  const needsConfirm = !!(quote && quote.needs_confirmation);
  const blockedBecause = quote ? quote.blocked_because : "";

  // Bands, read from the manifest like everything else on this screen. Off
  // means no dots and nothing held: a job that does not use bands must not
  // gain a single thing to look at or a single reason it cannot build.
  const bandsOn = !!manifest.bands_on;
  const bands = bandsOn ? (manifest.bands || []) : [];
  // The chips keep their place in the widget when the switch is off, rather
  // than closing the gap, so turning bands on and off moves nothing.
  const chips = manifest.bands || [];
  // The widget's A, B and C are always in sight: greyed while bands are off,
  // live when they are on. Spenser, 2026-09-18: "When you click it on, that's
  // when the three things appear. I don't like that." A job that has never
  // had bands has an empty list until the switch goes on and the server gives
  // it these three (`default_bands` in app/server/photos.py), so the widget
  // names them itself until then. A test holds this copy to the server's
  // `LOCKED_BANDS`.
  const SWITCH_BRINGS = ["A", "B", "C"];
  const widgetChips = chips.length ? chips
    : SWITCH_BRINGS.map((letter) => ({ letter, name: letter }));
  const waiting = bandsOn ? inPhotos.filter((x) => !x.p.band).length : 0;
  // What the grid draws. A third view of the one list, made the same way as
  // `inPhotos` and `cutPhotos`, so every index is still the photograph's own
  // place in the job and dragging inside a band moves it in the real order.
  // Every count above reads `inPhotos`, never this, so the numbers keep
  // counting the whole job. With bands off there is no filter at all.
  const filter = bandsOn && chips.some((b) => b.letter === onlyBand) ? onlyBand : null;
  const gridPhotos = filter
    ? inPhotos.filter((x) => x.p.band === filter || stayed.includes(x.p.file))
    : inPhotos;
  const waitingText = `${waiting} photograph${waiting === 1 ? " is" : "s are"} waiting for a band`;

  const buildReady = inPhotos.length > 0 && allReviewed && waiting === 0
                     && !(facts && !facts.ready);
  // The quote has to be in hand before this can be pressed, and that is a
  // safety rule rather than a nicety. `toSend` falls back to counting
  // uncaptioned photographs when the estimate has not arrived, so the button
  // could read "Generate captions (61)" and be live while `needsConfirm` was
  // still false, which sent a sixty-one photograph run with no confirmation
  // shown. The server refused it, so nothing was ever spent, but what Mark saw
  // was a raw refusal instead of the window asking him to agree to the money.
  // Found while photographing this screen, not by a test.
  //
  // The count on the button is counted here, from the photographs on this
  // screen, and not read off the quote. Spenser, 2026-09-18: "The caption
  // button doesn't get smaller." The quote is asked for when the screen opens
  // and when the spending window opens, and on purpose not on every caption
  // saved (Colleen's network, 2026-09-14), so read off the quote the number
  // stood still while he typed. The window still quotes the server's own
  // count, asked for again as it opens. Both count the same photographs: the
  // screen never holds one whose file has gone. For the same reason a stale
  // "nothing to do" does not hold the button off once a box has been emptied.
  const emptyHere = inPhotos.filter((x) => !(x.p.caption || "").trim()).length;
  const canGenerate = !!quote && inPhotos.length > 0 && emptyHere > 0
                      && (!blockedBecause || blockedBecause === "nothing_to_do");
  // Refresh is stopped by the same two things a run is stopped by, and by
  // nothing else. `nothing_to_do` is not one of them: it means every
  // photograph already has a caption, which is precisely the job refresh
  // exists for. The price has to be in hand as well, because the figure
  // printed on the control is the agreement and a blank control agrees to
  // nothing.
  const canRefresh = !!quote && aiOn
                     && blockedBecause !== "no_key" && blockedBecause !== "local_only";
  const chosen = manifest.caption_style || "view";
  // The one this job starts on is shown first, whichever it is.
  const ordered = [...styles].sort((a, b) => (b.key === chosen) - (a.key === chosen));

  // His own photographs with the captions written from them, for the style he
  // is looking at right now. Null means the style window has nothing bought
  // for this style and draws the written specimens instead, which is what it
  // does while they are still being written, when there is no key, and when a
  // demo job refuses.
  const shownShots = (shots && shots.samples && shots.samples[showing])
    ? shots.samples[showing].map((line) => ({ caption: line.caption,
                                              src: thumbUrl(job, line.file) }))
    : null;

  // --- what is being made --------------------------------------------------
  const named = !!(facts && facts.ready && facts.filename);
  const docName = named ? facts.filename : NO_NAME;

  // --- what stops an action is said by the action ---------------------------
  // Never in a line above it. A grey control that leaves him guessing is the
  // defect this replaced, and the sentence above it was the other one: the old
  // copy announced a 60-photo wall that no longer exists.
  function buildStop() {
    if (busy) return "Wait for what is running to finish";
    if (inPhotos.length === 0) return "No photos in the report yet";
    if (!allReviewed) {
      return `Tick every caption you have read first. ${inPhotos.length - reviewedCount} left.`;
    }
    if (waiting > 0) return waitingText;
    if (facts && !facts.ready) return "The file cannot be named yet";
    return "";
  }
  function generateStop() {
    if (busy) return "Wait for what is running to finish";
    if (blockedBecause === "no_key" || !aiOn) {
      // Three facts and no fourth: what is missing, what to do about it, and
      // that he is not stuck. Said once, here, on the only control it stops.
      // It used to be two grey paragraphs above his photographs saying the
      // same thing in different words.
      return "Writing captions needs a key on this computer. Open Settings to "
             + "add one. You can still type every caption in yourself.";
    }
    if (blockedBecause === "local_only") {
      return "These photos are demo material kept for local testing, so they are not sent anywhere.";
    }
    if (quote && inPhotos.length > 0 && emptyHere === 0) return "Every photo already has a caption.";
    if (!quote) return "Working out the cost";
    if (inPhotos.length === 0) return "No photos in the report yet";
    return "";
  }
  const buildWhy = buildStop();
  const generateWhy = generateStop();

  // --- what is happening right now -----------------------------------------
  // Two classes of message and no third. Anything that needs his answer is a
  // window over the screen, because nothing can go on until he answers.
  // Everything else is one quiet line here, under the counts, in a slot that
  // keeps its height when it is empty. Nothing else may sit between the header
  // and the photographs: on 2026-09-04 this screen could stack eleven boxes
  // there, and he asked what happens when three or four pile up.
  const notes = [];
  if (error) notes.push({ kind: "wrong", said: error, x: () => setError(null) });
  if (busy || running) {
    notes.push({
      kind: "run",
      said: running ? (
        <>
          {running.requests > 1
            ? `Writing captions, request ${Math.min(running.request + 1, running.requests)} of ${running.requests}`
            : "Writing captions"}
          {" · "}{running.captioned} of {running.total} written
        </>
      ) : busy,
      pct: running && running.total
        ? Math.round((running.captioned / running.total) * 100) : null,
    });
  }
  if (done && done.created) notes.push({
    kind: "done",
    said: <><strong>{done.created}</strong> is ready</>,
    // Offered, never done for him. Opening a client's document without being
    // asked is not the app's decision to make.
    acts: (
      <>
        <button className="linky" onClick={() => onReveal("document")}>Open document</button>
        <button className="linky" onClick={() => onReveal("folder")}>Show in folder</button>
      </>
    ),
    x: () => setDone(null),
  });
  if (done && typeof done === "string") notes.push({
    kind: "done", said: done, x: () => setDone(null),
  });
  if (spent && !spentOpen) notes.push({
    kind: "done",
    said: spent.summary || spent.label,
    acts: <button className="linky" onClick={() => setSpentOpen(true)}>What it cost</button>,
    x: () => setSpent(null),
  });
  if (cutNote) notes.push({ kind: "done", said: cutNote, x: () => setCutNote("") });
  // The reviewed count and its action used to stand here. They moved into the
  // widget's bar on 2026-09-16, and they did not stay in both places: two
  // homes for one fact is how the left said "9 of 12 reviewed" while the box
  // said everything was done. The bar is where reviewing is answered now.
  if (waiting > 0) notes.push({ kind: "standing", said: waitingText });
  const note = notes.length ? notes[Math.min(at, notes.length - 1)] : null;

  // The document's own account of the last run, in full. It is a window
  // whenever it is not clean, and a click off the quiet line otherwise.
  const runAccount = spent && (
    <div className={`outcome outcome-${spent.state === "partial" ? "partial"
                      : spent.state === "failed" ? "failed"
                      : spent.calculated_cost === null || spent.calculated_cost === undefined
                        ? "unknown" : "done"}`}>
      {spent.summary && <p className="outcome-said">{spent.summary}</p>}
      <strong>{spent.label}</strong>
      {spent.calculated_cost !== null && spent.calculated_cost !== undefined ? (
        <> : <code>{showMoney(spent.calculated_cost)}</code> for {spent.captioned}{" "}
          {spent.captioned === 1 ? "caption" : "captions"}.</>
      ) : (
        <span className="cost-unavailable"> . {spent.note}</span>
      )}
      <div className="cost-after">
        {spent.tokens && (
          <>Measured usage: <code>{spent.tokens.input.toLocaleString()}</code> input tokens,{" "}
            <code>{spent.tokens.output.toLocaleString()}</code> output tokens
            {spent.tokens.cache_read ? <>, <code>{spent.tokens.cache_read.toLocaleString()}</code> cached</> : null}.
          </>
        )}
        {" "}{spent.calculated_cost !== null && spent.calculated_cost !== undefined ? spent.note : ""}
      </div>
      {spent.remaining && spent.remaining.length > 0 && (
        <div className="cost-after">
          <strong>{spent.remaining.length}</strong>{" "}
          {spent.remaining.length === 1 ? "photo is" : "photos are"} still without a caption:{" "}
          {spent.remaining.join(", ")}.
        </div>
      )}
    </div>
  );

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={(e) => { if (e.currentTarget === e.target) setDragging(false); }}
      onDrop={(e) => {
        e.preventDefault(); setDragging(false);
        // Only a drag that started outside this app is an add. A tile being
        // reordered also carries a file (the browser attaches the thumbnail
        // the tile is showing), and uploading that would silently duplicate
        // the photo at thumbnail size. Our own drag state is the only
        // reliable way to tell the two apart.
        if (dragFrom.current !== null) return;
        onFiles(e.dataTransfer.files);
      }}
    >
      {/* THE HEADER. Two things, one row. On the left what is being made,
          its numbers and the quiet line. On the right the one widget. The
          row grows to the widget and no further, and the widget's height is
          pinned in the stylesheet, so nothing inside it can push the
          photographs down. Spenser approved this on 2026-09-15. */}
      <div className="screen-head">
        <div className="made">
          {/* A screen that makes a file is named by that file. */}
          <div className="nameline">
            <h1 className={named ? "" : "unknown"} title={docName}>{docName}</h1>
            <button className="linky" onClick={() => setFixing(true)}>
              {named ? "Not right?" : "Enter it"}
            </button>
          </div>
          {/* Only the numbers that describe the file, and where its
              photographs came from. He chose that folder, so it is a
              reminder rather than an announcement, and the link is how he
              changes his mind. The test for it is whether an answer was
              RECORDED, not whether the recorded name has letters in it: the
              top of Photos is recorded as an empty name, and that is a
              decision. */}
          <p className="figures">
            {inPhotos.length} {inPhotos.length === 1 ? "photograph" : "photographs"}
            {" · "}{pagesIn} {pagesIn === 1 ? "page" : "pages"}
            {where && where.chosen != null && (
              <>
                {" · from "}
                <strong>{where.chosen || "the Photos folder itself"}</strong>
                <button className="linky" onClick={() => setAsked(true)}>
                  Use a different folder
                </button>
              </>
            )}
          </p>
          {/* The quiet line. One line, always there, never taller. When
              nothing is happening it holds no words and no dot, and it still
              holds its height, so the photographs sit at the same pixel. */}
          <div className={`quiet k-${note ? note.kind : "rest"}`}
               role="status" aria-live="polite">
            {note && (
              <>
                <span className="mark" />
                <span className="said">{note.said}</span>
                {note.pct !== null && note.pct !== undefined && (
                  <span className="thread"><span style={{ width: `${note.pct}%` }} /></span>
                )}
                {note.acts}
                {notes.length > 1 && (
                  <button className="more"
                          onClick={() => setAt((at + 1) % notes.length)}>
                    · {notes.length - 1} more
                  </button>
                )}
                {note.x && <CloseX onClose={note.x} what="this message" />}
              </>
            )}
          </div>
        </div>

        {/* THE WIDGET. One object, upper right, holding everything she can
            do, the two settings that shape what comes out, and a bar along
            the bottom that answers how she gets to done.

            Spenser approved this on 2026-09-16 after moving every piece
            himself. `docs/design/photos-widget.html` is the design and it
            wins over any judgement here; `photos-widget.md` beside it says
            why, in his numbers.

            The top row is SPREAD, not right. That is what puts Build photo
            pages against the left edge, which is what puts the photo button
            directly underneath it on the row below. Right-justifying floats
            Build inward and the button sits under nothing. */}
        <div className="screen-actions control-panel">
          <div className="w-row">
            {/* Filled red: it writes a Word document into a folder Mark
                keeps, and that cannot be taken back. One of the two reds on
                this screen, and both are things that cannot be undone. The
                colour law of 2026-09-08, docs/ROADMAP.md. */}
            <span className="act-wrap">
              <button className={`button${buildReady ? "" : " is-off"}`} onClick={onBuild}
                      disabled={!!busy || !buildReady}>
                Build photo pages
              </button>
              <span className="why" data-has={buildWhy ? "yes" : "no"}>{buildWhy}</span>
            </span>
            {/* Blue: it spends money, but a caption is a draft she can
                retype, clear or run again. Money is not the axis; being
                stuck is. */}
            <span className="act-wrap">
              <button className={`button secondary${canGenerate ? "" : " is-off"}`} onClick={openChooser}
                      disabled={!!busy || !canGenerate}>
                {canGenerate ? `Generate captions (${emptyHere})` : "Generate captions"}
              </button>
              <span className="why" data-has={generateWhy ? "yes" : "no"}>{generateWhy}</span>
            </span>
          </div>

          <div className="w-row two">
            {/* The photograph with a plus, not the words. It is pushed hard
                left so it lands under Build photo pages. */}
            <button className="w-icon" onClick={() => filePicker.current?.click()}
                    aria-label="Add photos" title="Add photos">
              <svg viewBox="0 0 23 15" fill="none" aria-hidden="true">
                <rect x="0.6" y="2.6" width="11.8" height="9.8" rx="1.4"
                      stroke="currentColor" strokeWidth="1.2" />
                <circle cx="4" cy="6" r="1.15" fill="currentColor" />
                <path d="M1.4 11.2 4.9 8.1l2.3 2 2.1-1.7 2.1 2.2" stroke="currentColor"
                      strokeWidth="1.2" strokeLinejoin="round" fill="none" />
                <g className="plus">
                  <path d="M16.6 4.6v4.8M14.2 7h4.8" stroke="currentColor"
                        strokeWidth="1.5" strokeLinecap="round" />
                </g>
              </svg>
            </button>
            <input ref={filePicker} type="file" multiple accept="image/*,.heic" style={{ display: "none" }}
              onChange={(e) => onFiles(e.target.files)} />
            {/* Two questions, so two controls that do not look like each
                other. Bands is on or off, so it is a switch. Photographs to a
                page is a value, so it is a track of values. */}
            <span className="w-name">Per page</span>
            <span className="values" role="group" aria-label="Photographs to a page">
              <button className={perPage === 3 ? "on" : ""}
                      aria-pressed={perPage === 3} disabled={!!busy}
                      aria-label="Three photographs to a page"
                      onClick={() => onPerPage(3)}>3</button>
              <button className={perPage === 6 ? "on" : ""}
                      aria-pressed={perPage === 6} disabled={!!busy}
                      aria-label="Six photographs to a page"
                      onClick={() => onPerPage(6)}>6</button>
            </span>
            <span className="w-sep" />
            <span className="w-name">Bands</span>
            <button className="switch" role="switch" aria-checked={bandsOn}
                    aria-label="Bands" disabled={!!busy}
                    onClick={() => { showBand(null); onBands({ bands_on: !bandsOn }); }}>
              <span className="knob" />
            </button>
            {/* Each chip is a filter. Click one and only that band's
                photographs show; click it again and they all do; click
                another and it switches. Screen only, and the counts do not
                follow it. Spenser, 2026-09-17. With bands off they stay where
                they are, greyed and not clickable, so nothing in the widget
                moves or appears when the switch changes. 2026-09-18. */}
            <span className={`w-chips${bandsOn ? "" : " off"}`}>
              {widgetChips.map((b) => (
                <button key={b.letter}
                        className={`w-chip${filter === b.letter ? " is-on" : ""}`}
                        disabled={!bandsOn}
                        aria-label={`Band ${b.letter}`} tabIndex={bandsOn ? 0 : -1}
                        aria-pressed={filter === b.letter}
                        title={b.name === b.letter ? `Band ${b.letter}` : b.name}
                        onClick={() => showBand(filter === b.letter ? null : b.letter)}>
                  {b.letter}
                </button>
              ))}
            </span>
          </div>

          {/* THE BAR. How she gets to done, and nothing else. It is not a
              notification pane: those stay on the left, one quiet line at a
              time. The moment the two merge, this box becomes something to
              clear rather than something to read. */}
          <div className="barline">
            {/* One pill: "N of M reviewed", where M is every photograph in the
                report. Who wrote each one is on the photograph, not here;
                three pills did not fit the box. Spenser, 2026-09-18.

                The tick means one thing only: everything is reviewed. Then
                the pill is the pale tick green with the tick in front. Until
                then it is amber, the widget's colour for what still needs
                him, with no tick. Once every photograph has words, the amber
                pill is also the offer to tick the lot: pressing it asks the
                same warning it always asked, and hovering it says so. It wore
                the tick and a green while it was the offer, and "✓ 11 of 12
                reviewed" read as done: Spenser, 2026-09-18, from 0.7.6.3. */}
            {allWritten && !barDone ? (
              <button className="pill hold act" disabled={!!busy}
                      aria-label="Mark every caption as reviewed"
                      title="Mark every caption as reviewed"
                      onClick={() => { setMarkingAll(true); setError(null); setDone(null); }}>
                <b>{barRead}</b>&nbsp;of&nbsp;<b>{barOf}</b>&nbsp;reviewed
              </button>
            ) : (
              <span className={`pill ${barDone ? "done" : "hold"}`}>
                {barDone && <>&#10003;&nbsp;</>}
                <b>{barRead}</b>&nbsp;of&nbsp;<b>{barOf}</b>&nbsp;reviewed
              </span>
            )}
            {/* Red, and a link rather than a button: "the same exact thing,
                just red". It is not here at all until there is something to
                lose, and the gap to the money is pushed by this, so when it
                goes the money still holds the right edge. */}
            {captioned > 0 && (
              <button className="clear linky" disabled={!!busy}
                      onClick={() => { setClearing(true); setDone(null); setError(null); }}>
                Clear captions
              </button>
            )}
            {/* The job-wide back, to the right of Clear captions. Grey until a
                clear has happened, then live. It spares what he changed:
                only the photographs still empty since the clear come back, so
                it is safe to press twice and it greys itself the moment there
                is nothing left for it to do. Spenser, 2026-09-17. Its words,
                "Restore cleared captions", are his, 2026-09-18. Grey says
                nothing: no hover text, only the screen-reader name, so it is
                never a nameless button. His words, 2026-09-17: "I don't
                think you need to say anything in the grey." */}
            <button className="bar-back" disabled={!canPutBackAll || !!busy}
                    aria-label="Restore cleared captions"
                    title={canPutBackAll ? "Restore cleared captions" : undefined}
                    onClick={onCaptionsBack}>
              <BackMark />
            </button>
            {/* Always there. Before anything is generated it is the estimate
                and wears a tilde, which is the one moment she most wants it.
                After, it is what the job has cost and the tilde comes off. */}
            {money !== null && (
              <span className="money">{captioned === 0 ? "~" : ""}{money}</span>
            )}
          </div>
        </div>
      </div>

      {/* THE CONTENT. Nothing stands between the header and this. */}
      {count === 0 ? (
        <div className="drop">
          <strong>Drag photos here</strong> or use Add photos. They are copied into this job's
          Photos folder and your originals stay untouched.
        </div>
      ) : (
        <div className="grid">
          {gridPhotos.map(({ p, i }) => (
            <figure key={p.file} style={{ margin: 0 }} draggable
              onDragStart={() => (dragFrom.current = i)}
              onDragOver={(e) => e.preventDefault()}
              onDragEnd={() => (dragFrom.current = null)}
              onDrop={(e) => {
                if (dragFrom.current === null) return;   // a real file: let the screen add it
                e.stopPropagation();
                drop(i);
              }}>
              {/* Not draggable itself. The tile around it is what gets
                  dragged; leaving the image draggable makes the browser hand
                  the thumbnail over as a file on every reorder.
                  No sentence says so. A hint lives on the thing, not as a
                  line of text: the photographs afford dragging. */}
              <span className="photo-frame">
                <img src={thumbUrl(job, p.file)} alt={p.file} title={p.file} draggable={false} />
                {/* Laid over the picture while its one caption is being
                    written, and gone when it arrives. A failure stays until
                    he puts it away. Before the take-out button in the
                    markup, so that button still sits on top and still
                    works. */}
                {said[p.file] && (
                  <span className={`photo-says${said[p.file].failed ? " is-failed" : ""}`}
                        role="status" aria-live="polite">
                    {said[p.file].failed ? (
                      <>
                        <span className="photo-says-words">{said[p.file].failed}</span>
                        <CloseX what="this message" onClose={() => setSaid((now) => {
                          const rest = { ...now };
                          delete rest[p.file];
                          return rest;
                        })} />
                      </>
                    ) : "Refreshing caption"}
                  </span>
                )}
                <button className="dot cut-dot" aria-label="Take out" title="Take out"
                        onClick={() => onCut(p.file)}>
                  <span aria-hidden="true">&times;</span>
                </button>
              </span>
              {/* Which folder inside Photos this one came from, and only when
                  it did not come from the folder he chose. Once he has picked
                  one, saying it again under all sixteen tiles is the same
                  fact sixteen times; what he needs to see is the odd one out.
                  The leaf name is shown and the whole path is the tooltip. */}
              {p.folder && p.folder !== (where && where.chosen) && (
                <div className="photo-source" title={p.folder}>
                  from {p.folder.split("/").filter(Boolean).pop()}
                </div>
              )}
              {/* A box, not a line: captions run four to twelve words and he
                  has to be able to read the whole thing without clicking in. */}
              <textarea placeholder="Caption..." rows={2}
                value={p.file in typing ? typing[p.file] : p.caption}
                onChange={(e) => setCaption(i, e.target.value)}
                onBlur={() => commitCaption(i)} />
              {/* Who wrote the caption, quietly, under it. Information, not a
                  control, and never in the row below, which is exactly full.
                  Always here so every tile's row sits at the same height;
                  empty when there is no caption. Read from `author`, which
                  the server puts on every caption (`author_of` in
                  app/server/photos.py). The words are Spenser's to change.
                  2026-09-18. */}
              <div className="who">
                {(p.caption || "").trim()
                  ? (p.author === "person" ? "Typed" : p.author === "ai" ? "AI" : "")
                  : ""}
              </div>
              {/* The tick is the first thing in the row and stays there,
                  however many bands the job grows. Spenser, 2026-09-07. It
                  is one photograph at a time, with the all-at-once shortcut
                  kept behind its warning. */}
              <div className="review-line">
                <button className={`dot tick-dot${p.reviewed ? " is-reviewed" : ""}`}
                        disabled={!(p.caption || "").trim()}
                        aria-label={p.reviewed ? "Reviewed" : "Mark reviewed"}
                        title={(p.caption || "").trim()
                               ? (p.reviewed ? "Reviewed" : "Mark reviewed")
                               : "Write a caption first"}
                        onClick={() => onReview(p.file, !!p.reviewed)}>
                  <span aria-hidden="true">&#10003;</span>
                </button>
                {/* One dot per band, in band order. Clicking the band it is
                    already in takes it back out.

                    Drawn from the job's whole band list, `chips`, and not
                    from `bands`, so that with the switch off they are still
                    here holding their slots, hidden. That is the whole of
                    what keeps the tick, Back and refresh on the same pixel
                    whether bands are on or off: a class, `visibility:
                    hidden`, no tab stop. The widget's chips did the same
                    until 2026-09-18 and are greyed in sight now; these are
                    unchanged.

                    Off they are also `disabled` and carry no `is-on`. Hidden
                    is not gone, and a job that does not use bands must not
                    be able to have a photograph put into one. */}
                {chips.map((b) => (
                  <button key={b.letter}
                          className={`dot band-dot${bandsOn ? "" : " off"}${
                            bandsOn && p.band === b.letter ? " is-on" : ""}`}
                          disabled={!bandsOn}
                          tabIndex={bandsOn ? 0 : -1}
                          aria-label={`Put in band ${b.letter}`}
                          title={b.name === b.letter ? `Band ${b.letter}` : b.name}
                          onClick={() => onBand(p.file, p.band === b.letter ? null : b.letter)}>
                    <span aria-hidden="true">{b.letter}</span>
                  </button>
                ))}
                {/* Back, on this one photograph. A circle, the same 26 by 26
                    the tick and the bands are: Spenser, 2026-09-17, *"The
                    actual app is circles, and you gave me little ovals."* It
                    is live exactly when this photograph has words waiting,
                    and it needs nothing else to have happened first. Grey
                    says nothing: no hover text, only its name. */}
                <button className="dot back-dot"
                        disabled={!(p.cleared_caption || "").trim() || !!busy}
                        aria-label="Put the old caption back"
                        title={(p.cleared_caption || "").trim()
                               ? "Put the old caption back" : undefined}
                        onClick={() => onCaptionBack(p.file)}>
                  <BackMark />
                </button>
                {/* Refresh. The only control on the row that is not a circle,
                    because the price rides inside it, and the only one that
                    spends. The figure printed on it IS the agreement: one
                    photograph at a price he can read is not a number that
                    needs a window in front of it. */}
                <button className="dot refresh-dot"
                        disabled={!canRefresh || !!busy}
                        aria-label={onePhotoCents === null
                                    ? "Write a new caption"
                                    : `Write a new caption, about ${onePhotoCents} cents`}
                        title={onePhotoPrice === null
                               ? "Write a new caption"
                               : `Write a new caption, ~${onePhotoPrice}`}
                        onClick={() => onRefreshCaption(p.file)}>
                  <RefreshMark />
                  {onePhotoPrice !== null && (
                    <span className="price">~{onePhotoPrice}</span>
                  )}
                </button>
              </div>
            </figure>
          ))}
        </div>
      )}

      {/* Cut photos wait at the bottom, out of the way but never hidden, and
          the section is shut until he asks for it. Nothing here has been
          moved or deleted on disk. */}
      {cutPhotos.length > 0 && (
        <div className="cut-section">
          <button className="cut-head" onClick={() => setShowCut(!showCut)}>
            <span className="cut-caret">{showCut ? "▾" : "▸"}</span>
            Taken out ({cutPhotos.length})
          </button>
          {showCut && (
            <>
              <p className="setting-fine" style={{ margin: `0 0 ${k(12)}` }}>
                These are left out of the photo pages and out of caption writing.
                The files are still in the job's Photos folder, untouched.
              </p>
              <div className="grid">
                {cutPhotos.map(({ p }) => (
                  <figure key={p.file} className="is-cut" style={{ margin: 0 }}>
                    <img src={thumbUrl(job, p.file)} alt={p.file} title={p.file} draggable={false} />
                    {p.folder && p.folder !== (where && where.chosen) && (
                      <div className="photo-source" title={p.folder}>
                        from {p.folder.split("/").filter(Boolean).pop()}
                      </div>
                    )}
                    {p.caption ? (
                      <p className="cut-caption">{p.caption}</p>
                    ) : (
                      <p className="cut-caption empty">No caption</p>
                    )}
                    <button className="linky cut-link" onClick={() => onBringBack(p.file)}>
                      Bring back
                    </button>
                  </figure>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {dragging && count > 0 && (
        <div className="drag-hint">Drop to add these photos to the job</div>
      )}

      {/* WHAT NEEDS HIS ANSWER. A window over the screen, because nothing can
          go on until he answers, and nothing behind it moves while it is
          open. One at a time: no window opens on top of another. */}

      {/* Generating captions is one window. The cost in its upper right, the
          two styles as a toggle, his own first photographs captioned in the
          lit style, one confirm and one cancel. Spenser, 2026-09-14: *"I want
          one screen"*. The second window that used to open on top of this
          one, quoting the same money again, is gone.
          The style is a setting, so the toggle takes effect as he clicks it;
          Cancel backs out of the spending, not out of the setting. */}
      {asking && (
        <div className="sheet-back" onClick={(e) => { if (e.target === e.currentTarget) setAsking(false); }}>
          <div className="sheet wide" role="dialog" aria-modal="true"
               aria-label={`Generate captions for ${toSend} ${toSend === 1 ? "photo" : "photos"}?`}>
            {/* The money in the top right corner. Spenser asked for that on
                2026-09-04, on 2026-09-07 and again on 2026-09-14. It is a
                figure he glances at, not a warning, so it carries no box, no
                rule and no colour of its own. The count is in the title, so
                it is not said twice. */}
            <div className="sheet-head">
              <h2>Generate captions for {toSend} {toSend === 1 ? "photo" : "photos"}?</h2>
              {quote && quote.estimate && (
                <p className="sheet-cost">{showMoney(quote.estimate.total)} max</p>
              )}
            </div>

            {/* Two styles, and the lit half is the one this job is on. It used
                to carry the word "suggested" over that half. Spenser,
                2026-09-04: *"Who's suggesting it, right? Pull off the
                suggestion."* */}
            <div className="toggle">
              {ordered.map((s) => (
                <button key={s.key} className={showing === s.key ? "on" : ""}
                  onClick={() => setShowing(s.key)}>
                  <span className="toggle-label">{s.label}</span>
                </button>
              ))}
            </div>

            {/* One page, as a table: photo cells on the left, caption cells on
                the right with a rule between them, exactly the way
                photo_pages.py builds the real thing. Three-up is one
                photograph beside its caption. Six-up is two photographs above
                their two captions. */}
            <div className={`page-preview${perPage === 6 ? " is-six" : ""}`}
                 data-testid="page-preview">
              {previewRows(styles.find((s) => s.key === showing)?.samples || [],
                           perPage, shownShots)}
            </div>

            {/* Two states, never a mixture. While his own are being written
                the frames stay blank, because a written specimen beside a
                photograph reads as a caption of that photograph. */}
            {!shownShots && (
              <p className="sub" style={{ margin: `${k(10)} 0 0`, fontSize: k(12.5) }}>
                {shotsBusy
                  ? "Captioning your photographs..."
                  : "Examples of the style, not your photographs."}
              </p>
            )}

            {shotsError && (
              <p className="sub sample-trouble" style={{ margin: `${k(10)} 0 0` }}>{shotsError}</p>
            )}

            {/* No sentence under the samples. The one that stood here
                explained that a long run is split into requests and each is
                saved as it finishes: a fact about a failure that has not
                happened, on the screen where he is deciding to spend. If a
                run does stop partway, the account of it says so at the moment
                it happens. */}
            <div className="sheet-acts">
              <button className="linky" onClick={() => setAsking(false)}>Cancel</button>
              <button className="button secondary" onClick={() => beginCaptions(showing)}>
                Generate captions{quote && quote.estimate
                  ? ` (${showMoney(quote.estimate.total)})` : ""}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* What the last run did, when it is not a clean one. Three outcomes,
          three treatments: a run that saved some captions and not others is
          neither a success nor a failure, and a cost the provider did not
          report is not good news. */}
      {spentOpen && spent && (
        <div className="sheet-back" onClick={(e) => { if (e.target === e.currentTarget) setSpentOpen(false); }}>
          <div className="sheet" role="dialog" aria-modal="true" aria-label="What the run did">
            {runAccount}
            <div className="sheet-acts">
              <button className="linky" onClick={() => { setSpentOpen(false); setSpent(null); }}>
                Close
              </button>
              {spent.remaining && spent.remaining.length > 0 && (
                <button className="button secondary" disabled={!!busy}
                        onClick={() => { setSpentOpen(false); runCaptions(manifest.caption_style); }}>
                  Retry remaining {spent.remaining.length}{" "}
                  {spent.remaining.length === 1 ? "photo" : "photos"}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Never a plain button. Spenser, 2026-09-03: it is very important that
          humans review everything AI does. So the words say what it removes
          and he chooses. */}
      {markingAll && (
        <div className="sheet-back" onClick={(e) => { if (e.target === e.currentTarget) setMarkingAll(false); }}>
          <div className="sheet" role="dialog" aria-modal="true"
               aria-label="Mark every caption as reviewed?">
            <h2>Mark every caption as reviewed?</h2>
            <p className="fine">
              This removes the human check on what the model wrote. Captions with
              nothing written stay unread.
            </p>
            <div className="sheet-acts">
              <button className="linky" onClick={() => setMarkingAll(false)}>Cancel</button>
              <button className="button secondary" onClick={onMarkAll}>Mark them all</button>
            </div>
          </div>
        </div>
      )}

      {/* Cannot be undone, and not why he came to this screen, so the button
          carries the red without the fill. The colour law of 2026-09-08. */}
      {clearing && (
        <div className="sheet-back" onClick={(e) => { if (e.target === e.currentTarget) setClearing(false); }}>
          <div className="sheet" role="dialog" aria-modal="true"
               aria-label="Clear the captions?">
            <h2>Clear {captioned} {captioned === 1 ? "caption" : "captions"}?</h2>
            <p className="fine">
              The photographs, their order and the caption style are unchanged.
            </p>
            <div className="sheet-acts">
              <button className="linky" onClick={() => setClearing(false)}>Cancel</button>
              <button className="button final" onClick={onClearCaptions} disabled={!!busy}>
                Clear {captioned} {captioned === 1 ? "caption" : "captions"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* The city and the address the built file is named from. Read out of
          the brief, which means split out of one line of text, so a wrong
          split has to be visible before it becomes a filename rather than
          after. Asked as a window, because it is a question. */}
      {fixing && (
        <div className="sheet-back" onClick={(e) => { if (e.target === e.currentTarget) setFixing(false); }}>
          <div className="sheet" role="dialog" aria-modal="true"
               aria-label="What is the file called?">
            <h2>What is the file called?</h2>
            {facts && !facts.ready && (
              <p className="fine">
                The {facts.missing.join(" and ")} could not be read from this
                job's brief.
              </p>
            )}
            <div className="setting-actions" style={{ marginTop: k(14), gap: k(8), flexWrap: "wrap" }}>
              <label className="setting-fine" style={{ margin: 0 }}>City
                <input defaultValue={facts ? facts.city : ""} id="fix-city" style={{ marginLeft: k(6) }} />
              </label>
              <label className="setting-fine" style={{ margin: 0 }}>Street address
                <input defaultValue={facts ? facts.address : ""} id="fix-address" style={{ marginLeft: k(6) }} />
              </label>
            </div>
            <div className="sheet-acts">
              <button className="linky" onClick={() => setFixing(false)}>Cancel</button>
              <button className="button secondary" onClick={() => onFixFacts(
                document.getElementById("fix-city").value,
                document.getElementById("fix-address").value)}>Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
