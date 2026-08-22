import React, { useEffect, useRef, useState } from "react";
import { getManifest, putManifest, uploadPhotos, draftCaptions, build, thumbUrl, captionStyles, clearCaptions, cutPhoto, uncutPhoto,
         captionEstimate, markReviewed, markUnreviewed, jobFacts, putJobFacts, reveal } from "../api.js";

export default function PhotosScreen({ job }) {
  const [manifest, setManifest] = useState(null);
  const [styles, setStyles] = useState([]);
  const [asking, setAsking] = useState(false);   // the caption style step
  const [showing, setShowing] = useState(null);  // which style the examples are toggled to
  const [busy, setBusy] = useState("");
  const [done, setDone] = useState(null);
  const [error, setError] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [clearing, setClearing] = useState(false);  // the clear-captions step
  const [showCut, setShowCut] = useState(false);    // the Cut photos section
  const [cutNote, setCutNote] = useState("");
  const [aiOn, setAiOn] = useState(true);   // until the app says otherwise
  const [quote, setQuote] = useState(null);   // what a run would send and cost
  const [spent, setSpent] = useState(null);   // what the last run did cost
  const [facts, setFacts] = useState(null);   // city and address for the filename
  const [fixing, setFixing] = useState(false);
  const [confirming, setConfirming] = useState(null);  // the spend confirmation
  const dragFrom = useRef(null);
  const filePicker = useRef(null);

  useEffect(() => { getManifest(job).then(setManifest).catch((e) => setError(e.message)); }, [job]);
  useEffect(() => { jobFacts(job).then(setFacts).catch(() => {}); }, [job]);

  // Refreshed whenever the photos change, so the number he is shown before
  // spending money is the number for what is actually there now.
  const refreshQuote = React.useCallback(() => {
    captionEstimate(job).then(setQuote).catch(() => {});
  }, [job]);
  useEffect(() => { if (manifest) refreshQuote(); }, [manifest, refreshQuote]);
  useEffect(() => {
    captionStyles()
      .then((r) => { setStyles(r.styles); setAiOn(r.ai_available); })
      .catch(() => {});
  }, []);

  // Escape closes the step, the way every dialog on his computer already does.
  useEffect(() => {
    if (!asking) return;
    const onKey = (e) => { if (e.key === "Escape") setAsking(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [asking]);

  async function save(next) {
    setManifest(next);
    await putManifest(job, next).catch((e) => setError(e.message));
  }

  async function onFiles(files) {
    if (!files?.length) return;
    setBusy("Copying photos into the job folder..."); setError(null);
    try { setManifest(await uploadPhotos(job, files)); } catch (e) { setError(e.message); }
    setBusy("");
  }

  // Opens a step and nothing else. It reads no photograph, sends no
  // photograph, and calls nobody. Choosing how the captions should read used
  // to caption three of his photos both ways, which meant two paid requests
  // fired before he had seen a price or agreed to anything.
  function openChooser() {
    setShowing(manifest.caption_style || "view");
    setAsking(true);
  }

  // Above thirty photographs he sees the number in a window of its own before
  // anything is sent. Below that the estimate on the step is enough: the point
  // is proportion, not a second hurdle on a small job.
  function beginCaptions(style) {
    setAsking(false);
    if (needsConfirm) { setConfirming({ style }); return; }
    runCaptions(style, false);
  }

  async function runCaptions(style, confirmed) {
    setConfirming(null);
    setAsking(false);
    setBusy("Writing captions..."); setError(null); setSpent(null);
    try {
      if (style && style !== manifest.caption_style) {
        await save({ ...manifest, caption_style: style });
      }
      const m = await draftCaptions(job, confirmed || needsConfirm);
      setManifest(m);
      // What it actually cost, kept on screen next to what was estimated.
      if (m.measured) setSpent({ ...m.measured, captioned: m.captioned, remaining: m.remaining || [] });
      if (m.error) setError(m.error);
      if (!m.ai_available) {
        setError("Writing captions needs a key on this computer. You can still type them in yourself.");
      }
    } catch (e) { setError(e.message); }
    setBusy("");
    refreshQuote();
  }

  async function onReview(file, already) {
    setError(null);
    try {
      setManifest(already ? await markUnreviewed(job, file) : await markReviewed(job, file));
    } catch (e) { setError(e.message); }
  }

  async function onFixFacts(city, address) {
    try { setFacts(await putJobFacts(job, { city, address })); setFixing(false); }
    catch (e) { setError(e.message); }
  }

  async function onCut(file) {
    setError(null); setDone(null);
    try {
      setManifest(await cutPhoto(job, file));
      setCutNote("Moved to Cut photos. The original file was not changed.");
    } catch (e) { setError(e.message); }
  }

  async function onBringBack(file) {
    setError(null); setDone(null); setCutNote("");
    try { setManifest(await uncutPhoto(job, file)); }
    catch (e) { setError(e.message); }
  }

  async function onClearCaptions() {
    setClearing(false);
    setBusy("Clearing captions..."); setError(null); setDone(null);
    try {
      const m = await clearCaptions(job);
      setManifest(m);
      setDone(`${m.cleared} ${m.cleared === 1 ? "caption was" : "captions were"} cleared. `
              + "The photos, their order and the caption style are unchanged.");
    } catch (e) { setError(e.message); }
    setBusy("");
  }

  async function onBuild() {
    setBusy("Building photo pages..."); setError(null); setDone(null);
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
    const next = structuredClone(manifest);
    next.photos[i].caption = caption;
    setManifest(next);
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

  if (!manifest) return <p className="sub">Loading...</p>;

  const count = manifest.photos.length;
  const pages = Math.max(1, Math.ceil(count / 3));
  // Only captions with something in them can be cleared, so this is the
  // number the confirmation quotes and the number the server will act on.
  const written = manifest.photos.filter((p) => (p.caption || "").trim()).length;
  // A cut photo keeps its place in the array. These two views are only ever
  // filters of that one list, so nothing is reordered by cutting.
  const inPhotos = manifest.photos.map((p, i) => ({ p, i })).filter((x) => !x.p.cut);
  const cutPhotos = manifest.photos.map((p, i) => ({ p, i })).filter((x) => x.p.cut);
  const pagesIn = Math.max(1, Math.ceil(inPhotos.length / 3));

  // Review, counted from the manifest so the screen and the server agree even
  // if one of them is a moment stale.
  const reviewedCount = inPhotos.filter((x) => x.p.reviewed).length;
  const allReviewed = inPhotos.length > 0 && reviewedCount === inPhotos.length;
  const reviewText = `${reviewedCount} of ${inPhotos.length} reviewed`;

  // Everything the server told us about this run, read before anything that
  // depends on it. Declared out of order once and the whole screen went blank
  // on a temporal-dead-zone error, which no test caught because none of them
  // render React.
  const toSend = quote ? quote.photos_to_send : inPhotos.filter((x) => !(x.p.caption || "").trim()).length;
  const ceiling = quote ? quote.tranche_size : 60;
  const tranches = quote ? quote.tranches : 1;
  const needsConfirm = !!(quote && quote.needs_confirmation);
  const blockedBecause = quote ? quote.blocked_because : "";

  const buildReady = inPhotos.length > 0 && allReviewed && !(facts && !facts.ready);
  const canGenerate = inPhotos.length > 0 && !blockedBecause && toSend > 0;
  const chosen = manifest.caption_style || "view";
  // The one this job starts on is shown first, whichever it is.
  const ordered = [...styles].sort((a, b) => (b.key === chosen) - (a.key === chosen));

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
      {/* Actions sit at the top, next to the title. The photos are what he
          came here to look at, so nothing goes above them but this row. */}
      <div className="screen-head">
        <div>
          <h1 style={{ margin: 0 }}>Photos</h1>
          <p className="sub" style={{ margin: "4px 0 0" }}>
            Included: {inPhotos.length} · Cut: {cutPhotos.length}
            {" "}· about {pagesIn} {pagesIn === 1 ? "page" : "pages"}.
            {" "}Drag a photo to reorder it.
          </p>
          {inPhotos.length > 0 && (
            <p className={`sub review-progress${allReviewed ? " is-done" : ""}`} style={{ margin: "6px 0 0" }}>
              {reviewText}{allReviewed ? ". Ready to build." : ". Build waits until you have read them all."}
            </p>
          )}
          {/* Whenever the button is off, this says why in words. A grey
              control that leaves him guessing is the defect this replaced:
              the old copy here announced a 60-photo wall that no longer
              exists, and he read it as the app being broken. */}
          {blockedBecause === "no_key" && (
            <p className="sub off-note" style={{ margin: "6px 0 0" }}>
              Writing captions needs a key on this computer. Open Settings to
              add one. You can still type every caption in yourself.
            </p>
          )}
          {blockedBecause === "local_only" && (
            <p className="sub off-note" style={{ margin: "6px 0 0" }}>
              These photos are demo material kept for local testing, so they
              are not sent anywhere. Everything else on this screen works.
            </p>
          )}
          {blockedBecause === "nothing_to_do" && inPhotos.length > 0 && (
            <p className="sub off-note" style={{ margin: "6px 0 0" }}>
              Every photo in the report already has a caption.
            </p>
          )}
          {toSend > 0 && tranches > 1 && (
            <p className="sub" style={{ margin: "6px 0 0" }}>
              {toSend} photos will be written in {tranches} goes of up to{" "}
              {ceiling}. Captions are saved as each one finishes.
            </p>
          )}
          {!aiOn && (
            <p className="sub off-note" style={{ margin: "6px 0 0" }}>
              Writing captions for you is off: no key is set up on this computer.
              You can still type every caption in yourself, and everything else works.
            </p>
          )}
        </div>
        <div className="screen-actions">
          <div className="action-row">
            {/* Off means off, and it looks off. The brand red at half opacity
                still reads as a button he should be able to press, which is
                the same defect the Suggest captions button was given `is-off`
                to avoid. Found by looking at the screen, not by a test. */}
            <button className={`button${buildReady ? "" : " is-off"}`} onClick={onBuild}
                    disabled={!!busy || !buildReady}
                    title={inPhotos.length === 0 ? "No photos in the report yet"
                           : !allReviewed ? "Tick every caption you have read first"
                           : facts && !facts.ready ? "The file cannot be named yet" : ""}>
              Build photo pages
            </button>
            {/* Off means off, and it looks off. A blue button at half opacity
                still reads as a button he should be able to press. */}
            <button className={`button secondary${canGenerate ? "" : " is-off"}`} onClick={openChooser}
                    disabled={!!busy || !canGenerate}
                    title={blockedBecause === "no_key" ? "Needs a key on this computer"
                           : blockedBecause === "local_only" ? "Demo photos are not sent anywhere"
                           : blockedBecause === "nothing_to_do" ? "Every photo already has a caption" : ""}>
              {canGenerate ? `Generate captions (${toSend})` : "Generate captions"}
            </button>
            <button className="linky" style={{ marginLeft: 0 }} onClick={() => filePicker.current?.click()}>
              Add photos
            </button>
            {/* Nothing to clear means nothing offered, rather than a button
                that does nothing when pressed. */}
            {written > 0 && (
              <button className="linky" style={{ marginLeft: 0 }} disabled={!!busy}
                      onClick={() => { setClearing(true); setDone(null); setError(null); }}>
                Clear captions
              </button>
            )}
            <input ref={filePicker} type="file" multiple accept="image/*,.heic" style={{ display: "none" }}
              onChange={(e) => onFiles(e.target.files)} />
          </div>
          {/* Something has to move while the model is looking at the photos.
              Writing a dozen captions takes real seconds, and a screen that
              sits still reads as broken. */}
          {busy && (
            <div className="working">
              <div className="loading-bar"><span /></div>
              <span className="working-text">{busy}</span>
            </div>
          )}
        </div>
      </div>

      {/* Asked here, as a step inside the action he clicked, and it names the
          job because this screen is reached from more than one. */}
      {clearing && (
        <div className="confirm" style={{ marginTop: 0, marginBottom: 16 }}>
          <p style={{ margin: "0 0 10px" }}>
            Clear <strong>{written}</strong> {written === 1 ? "caption" : "captions"} in{" "}
            <strong>{job}</strong>?
          </p>
          <p className="setting-fine" style={{ margin: "0 0 12px" }}>
            The photos, their order, the caption style and everything else about this
            job stay as they are, and no built Word file is removed. Cleared captions
            cannot be recovered. Suggest captions can write new ones afterwards.
          </p>
          <div className="setting-actions">
            <button className="button" onClick={onClearCaptions} disabled={!!busy}>
              Clear {written} {written === 1 ? "caption" : "captions"}
            </button>
            <button className="linky" onClick={() => setClearing(false)}>Cancel</button>
          </div>
        </div>
      )}

      {/* What the last run cost, from what the provider reported. Kept next to
          what was estimated so the two can be compared, and never called an
          actual cost, because it is this app's arithmetic and not a bill. */}
      {spent && (
        <div className="done" style={{ marginTop: 0, marginBottom: 16 }}>
          <strong>{spent.label}</strong>
          {spent.calculated_cost !== null && spent.calculated_cost !== undefined ? (
            <> : <code>${spent.calculated_cost.toFixed(2)}</code> for {spent.captioned}{" "}
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
              {spent.remaining.join(", ")}. The captions already written are saved and
              will not be paid for again.
              <div style={{ marginTop: 8 }}>
                <button className="button secondary" disabled={!!busy}
                        onClick={() => runCaptions(manifest.caption_style)}>
                  Retry remaining {spent.remaining.length}{" "}
                  {spent.remaining.length === 1 ? "photo" : "photos"}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* The city and the address the built file will be named from, next to
          the action that uses them. Read out of the brief, which means split
          out of one line of text, so a wrong split has to be visible before it
          becomes a filename rather than after. */}
      {/* Where it will be saved, until it is saved. Once the document exists
          the completion message below says the same thing about a real file,
          so keeping both on screen was one fact told twice. */}
      {facts && inPhotos.length > 0 && !done && (
        <div className="done" style={{ marginTop: 0, marginBottom: 16 }}>
          {facts.ready ? (
            <>Will be saved as <strong>{facts.filename}</strong>.</>
          ) : (
            <span className="cost-unavailable">
              The {facts.missing.join(" and ")} could not be read from this job's
              brief, so the file cannot be named yet.
            </span>
          )}
          {!fixing && (
            <button className="linky" style={{ marginLeft: 8 }} onClick={() => setFixing(true)}>
              {facts.ready ? "Not right?" : "Enter it"}
            </button>
          )}
          {fixing && (
            <div className="setting-actions" style={{ marginTop: 10, gap: 8, flexWrap: "wrap" }}>
              <label className="setting-fine">City
                <input defaultValue={facts.city} id="fix-city" style={{ marginLeft: 6 }} />
              </label>
              <label className="setting-fine">Street address
                <input defaultValue={facts.address} id="fix-address" style={{ marginLeft: 6 }} />
              </label>
              <button className="button" onClick={() => onFixFacts(
                document.getElementById("fix-city").value,
                document.getElementById("fix-address").value)}>Save</button>
              <button className="linky" onClick={() => setFixing(false)}>Cancel</button>
            </div>
          )}
        </div>
      )}

      {cutNote && <div className="done" style={{ marginTop: 0, marginBottom: 16 }}>{cutNote}</div>}

      {/* Clearing captions reports itself here too, as a plain sentence. Only
          a build carries a file, and only a file gets the two actions. */}
      {done && typeof done === "string" && (
        <div className="done" style={{ marginTop: 0, marginBottom: 16 }}>{done}</div>
      )}

      {done && done.created && (
        <div className="finished">
          <div className="finished-said">
            <strong>{done.created}</strong> is ready.
            <span className="finished-where">Saved in this job's Photos folder. Nothing was overwritten.</span>
          </div>
          {/* Offered, never done for him. Opening a client's document without
              being asked is not the app's decision to make. */}
          <div className="finished-acts">
            <button className="button" onClick={() => onReveal("document")}>Open document</button>
            <button className="button secondary" onClick={() => onReveal("folder")}>Show in folder</button>
          </div>
        </div>
      )}
      {error && <div className="error" style={{ marginTop: 0, marginBottom: 16 }}>{error}</div>}

      {count === 0 ? (
        <div className="drop">
          <strong>Drag photos here</strong> or use Add photos. They are copied into this job's
          Photos folder and your originals stay untouched.
        </div>
      ) : (
        <div className="grid">
          {inPhotos.map(({ p, i }) => (
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
                  the thumbnail over as a file on every reorder. */}
              <img src={thumbUrl(job, p.file)} alt={p.file} title={p.file} draggable={false} />
              {/* A box, not a line: captions run four to twelve words and he
                  has to be able to read the whole thing without clicking in. */}
              <textarea value={p.caption} placeholder="Caption..." rows={2}
                onChange={(e) => setCaption(i, e.target.value)}
                onBlur={() => save(manifest)} />
              {/* Directly under the caption, and a real target rather than a
                  tick in a corner. It is not called Approve, and there is
                  deliberately no way to do all of them at once: the point is
                  that he has read each one. */}
              <div className="review-line">
                <button className={`review-btn${p.reviewed ? " is-reviewed" : ""}`}
                        disabled={!(p.caption || "").trim()}
                        title={(p.caption || "").trim() ? "" : "Write a caption first"}
                        onClick={() => onReview(p.file, !!p.reviewed)}>
                  {p.reviewed ? "Reviewed" : "Mark reviewed"}
                </button>
                <button className="linky cut-link" style={{ marginLeft: 0 }}
                        onClick={() => onCut(p.file)}>
                  Cut from report
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
            Cut photos ({cutPhotos.length})
          </button>
          {showCut && (
            <>
              <p className="setting-fine" style={{ margin: "0 0 12px" }}>
                These are left out of the report and out of caption writing. The
                files are still in the job's Photos folder, untouched.
              </p>
              <div className="grid">
                {cutPhotos.map(({ p }) => (
                  <figure key={p.file} className="is-cut" style={{ margin: 0 }}>
                    <img src={thumbUrl(job, p.file)} alt={p.file} title={p.file} draggable={false} />
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

      {/* The caption style is asked here, as a step, because it is a question
          about the thing he just clicked. Parked on the page it was invisible. */}
      {/* The spend, in a window of its own, with the count and the amount
          calculated rather than written here. Nothing is sent until he
          presses the button on the right. */}
      {confirming && quote && (
        <div className="sheet-back" onClick={(e) => { if (e.target === e.currentTarget) setConfirming(null); }}>
          <div className="sheet spend" role="dialog" aria-modal="true"
               aria-label={`Generate captions for ${toSend} photos?`}>
            <h2>Generate captions for {toSend} {toSend === 1 ? "photo" : "photos"}?</h2>

            <div className="spend-figure">
              <span className="spend-label">Estimated maximum cost</span>
              <span className="spend-amount">${quote.estimate.total.toFixed(2)}</span>
            </div>

            <p className="setting-fine" style={{ margin: "14px 0 0" }}>
              {tranches > 1
                ? `The work is divided into ${tranches} requests of up to ${ceiling} photos. Captions are saved as each request finishes.`
                : "The work may be divided into multiple requests. Captions are saved as each request finishes."}
            </p>

            <div className="spend-warning">
              If you continue, generating captions for {toSend}{" "}
              {toSend === 1 ? "photo" : "photos"} may cost up to{" "}
              <strong>${quote.estimate.total.toFixed(2)}</strong>.
            </div>

            <div className="setting-actions" style={{ marginTop: 18 }}>
              <button className="linky" onClick={() => setConfirming(null)}>Cancel</button>
              <button className="button" onClick={() => runCaptions(confirming.style, true)}>
                Generate captions
              </button>
            </div>
          </div>
        </div>
      )}

      {asking && (
        <div className="sheet-back" onClick={(e) => { if (e.target === e.currentTarget) setAsking(false); }}>
          <div className="sheet" role="dialog" aria-modal="true" aria-label="How should the captions read?">
            <h2>How should the captions read?</h2>
            <p className="sub" style={{ margin: "0 0 16px" }}>
              Two examples of each style, and how the printed page is laid out.
              Nothing is sent and nothing is charged for until you confirm.
            </p>

            {/* The money, before the button that spends it, and shown as the
                arithmetic rather than as a total he has to take on trust. It
                is a maximum: the rounding only ever goes up, and the rate
                starts high and comes down as real runs are measured. */}
            {quote && quote.estimate && toSend > 0 && (
              <div className="confirm" style={{ margin: "0 0 16px" }}>
                <p className="cost-line" style={{ margin: "0 0 8px" }}>
                  <strong>{quote.estimate.label}</strong> for{" "}
                  {toSend} {toSend === 1 ? "photo" : "photos"}:
                </p>
                <div className="cost-arith">{quote.estimate.arithmetic}</div>
                <p className="setting-fine" style={{ margin: "10px 0 0" }}>
                  An estimate, rounded up. The real cost is measured from what
                  Anthropic reports and shown here afterwards. Photos that already
                  have a caption are not sent and are not charged for again.
                </p>
              </div>
            )}

            {/* One page, as a table: photo cells on the left, caption cells on
                the right with a rule between them, exactly the way
                photo_pages.py builds the real thing. The toggle sits at the
                head of the caption column, because that is the column it
                changes. */}
            <div className="page-preview">
              <div className="cell-photo head" />
              <div className="cell-caption head">
                {/* The recommendation is a flag above the option it names,
                    following the design system's segmented control, rather
                    than a second word sitting inside the label. Which option
                    carries it is unchanged: still the job's own caption
                    style, defaulting to View of. */}
                <div className="toggle">
                  {ordered.map((s) => (
                    <button key={s.key} className={showing === s.key ? "on" : ""}
                      onClick={() => setShowing(s.key)}>
                      {s.key === (manifest.caption_style || "view") && (
                        <span className="toggle-flag">suggested</span>
                      )}
                      <span className="toggle-label">{s.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Written examples beside an empty frame, never beside one of
                  his photographs. A line of text sitting next to a real photo
                  reads as a caption OF that photo, and the app has not looked
                  at it and cannot say. The frame is deliberately blank. */}
              {(styles.find((s) => s.key === showing)?.samples || []).map((line, n) => (
                <React.Fragment key={`${showing}-${n}`}>
                  <div className="cell-photo is-example" aria-hidden="true" />
                  <div className="cell-caption">{line}</div>
                </React.Fragment>
              ))}
            </div>

            <p className="sub" style={{ margin: "10px 0 0", fontSize: 12.5 }}>
              Examples of the writing style, not captions of your photographs.
            </p>

            <div className="sheet-foot">
              <p className="keep-note">Captions you have already typed are never changed.</p>
              <button className="button" onClick={() => beginCaptions(showing)}>
                Use this style
              </button>
              <button className="linky" onClick={() => setAsking(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
