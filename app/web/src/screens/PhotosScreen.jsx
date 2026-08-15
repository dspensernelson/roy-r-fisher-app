import React, { useEffect, useRef, useState } from "react";
import { getManifest, putManifest, uploadPhotos, draftCaptions, build, thumbUrl, captionStyles, captionPreview, clearCaptions, cutPhoto, uncutPhoto } from "../api.js";

export default function PhotosScreen({ job }) {
  const [manifest, setManifest] = useState(null);
  const [styles, setStyles] = useState([]);
  const [asking, setAsking] = useState(false);   // the caption style step
  const [preview, setPreview] = useState(null);  // his own photos, captioned both ways
  const [previewing, setPreviewing] = useState(false);
  const [showing, setShowing] = useState(null);  // which style the preview is toggled to
  const [busy, setBusy] = useState("");
  const [done, setDone] = useState(null);
  const [error, setError] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [clearing, setClearing] = useState(false);  // the clear-captions step
  const [showCut, setShowCut] = useState(false);    // the Cut photos section
  const [cutNote, setCutNote] = useState("");
  const [aiOn, setAiOn] = useState(true);   // until the app says otherwise
  const dragFrom = useRef(null);
  const filePicker = useRef(null);

  useEffect(() => { getManifest(job).then(setManifest).catch((e) => setError(e.message)); }, [job]);
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

  async function openChooser() {
    setShowing(manifest.caption_style || "view");
    setAsking(true);
    if (preview) return;                    // asked once per visit, not per open
    setPreviewing(true);
    try { setPreview(await captionPreview(job)); } catch (e) { setError(e.message); }
    setPreviewing(false);
  }

  async function runCaptions(style) {
    setAsking(false);
    setBusy("Writing captions..."); setError(null);
    try {
      if (style && style !== manifest.caption_style) {
        await save({ ...manifest, caption_style: style });
      }
      const m = await draftCaptions(job);
      setManifest(m);
      if (!m.ai_available) {
        setError("Writing captions needs a key on this computer. You can still type them in yourself.");
      }
    } catch (e) { setError(e.message); }
    setBusy("");
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
    try { setDone((await build(job)).created); } catch (e) { setError(e.message); }
    setBusy("");
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
          {!aiOn && (
            <p className="sub off-note" style={{ margin: "6px 0 0" }}>
              Writing captions for you is off: no key is set up on this computer.
              You can still type every caption in yourself, and everything else works.
            </p>
          )}
        </div>
        <div className="screen-actions">
          <div className="action-row">
            <button className="button" onClick={onBuild}
                    disabled={!!busy || inPhotos.length === 0}>
              Build photo pages
            </button>
            {/* Off means off, and it looks off. A blue button at half opacity
                still reads as a button he should be able to press. */}
            <button className={`button secondary${aiOn ? "" : " is-off"}`} onClick={openChooser}
                    disabled={!!busy || inPhotos.length === 0 || !aiOn}
                    title={aiOn ? "" : "Needs a key on this computer"}>
              Suggest captions
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

      {cutNote && <div className="done" style={{ marginTop: 0, marginBottom: 16 }}>{cutNote}</div>}

      {done && <div className="done" style={{ marginTop: 0, marginBottom: 16 }}>
        {typeof done === "string" && done.includes("cleared")
          ? done
          : <>Done. <strong>{done}</strong> was created in this job's Photos folder. Nothing was overwritten.</>}
      </div>}
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
              <button className="linky cut-link" onClick={() => onCut(p.file)}>
                Cut from report
              </button>
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
      {asking && (
        <div className="sheet-back" onClick={(e) => { if (e.target === e.currentTarget) setAsking(false); }}>
          <div className="sheet" role="dialog" aria-modal="true" aria-label="How should the captions read?">
            <h2>How should the captions read?</h2>
            <p className="sub" style={{ margin: "0 0 16px" }}>
              Your own photos, written both ways. This is how the printed page is laid out.
            </p>

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

              {previewing && (
                <>
                  <div className="cell-photo" />
                  <div className="cell-caption waiting">
                    <div className="loading-bar"><span /></div>
                    <p>Writing sample captions for three of your photos.<br />
                      This takes a few seconds.</p>
                  </div>
                </>
              )}

              {!previewing && preview && preview.photos.map((file) => (
                <React.Fragment key={file}>
                  <div className="cell-photo"><img src={thumbUrl(job, file)} alt="" /></div>
                  <div className="cell-caption">
                    {preview.ai_available
                      ? (preview.captions[showing]?.[file] || <em>no caption</em>)
                      : (styles.find((s) => s.key === showing)?.sample)}
                  </div>
                </React.Fragment>
              ))}
            </div>

            {!previewing && preview && !preview.ai_available && (
              <p className="sub" style={{ margin: "10px 0 0", fontSize: 12.5 }}>
                These are examples, not your photos. Writing real ones needs a key on this computer.
              </p>
            )}

            <div className="sheet-foot">
              <p className="keep-note">Captions you have already typed are never changed.</p>
              <button className="button" onClick={() => runCaptions(showing)} disabled={previewing}>
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
