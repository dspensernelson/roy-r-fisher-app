const { ScreenHead, Button, LinkButton, Working, Banner, PhotoGrid, PhotoTile,
        DropZone, Sheet, SegmentedControl, PagePreview, DragHint } = window.RoyRFisherDesignSystem_5d521b;

const SAMPLES = {
  view: ["West elevation and loading area", "Street frontage and parking", "Interior, sales floor"],
  facing: ["Looking east from 4th Street SW", "Looking north along the frontage", "Looking east from the entry"],
};

function PhotosScreen({ job }) {
  const [photos, setPhotos] = React.useState(job.photos === 0 ? [] : window.DEMO.photos);
  const [busy, setBusy] = React.useState("");
  const [done, setDone] = React.useState(null);
  const [asking, setAsking] = React.useState(false);
  const [showing, setShowing] = React.useState("view");
  const [previewing, setPreviewing] = React.useState(false);
  const [dragging, setDragging] = React.useState(false);
  const from = React.useRef(null);
  const styles = window.DEMO.captionStyles;

  const pages = Math.max(1, Math.ceil(photos.length / 3));
  const setCaption = (i, c) => setPhotos(photos.map((p, j) => (j === i ? { ...p, caption: c } : p)));

  function reorder(i) {
    if (from.current === null || from.current === i) return;
    const next = photos.slice();
    const [moved] = next.splice(from.current, 1);
    next.splice(i, 0, moved);
    from.current = null;
    setPhotos(next);
  }
  function openChooser() {
    setAsking(true); setPreviewing(true);
    setTimeout(() => setPreviewing(false), 1200);
  }
  function runCaptions() {
    setAsking(false); setBusy("Writing captions…");
    setTimeout(() => {
      setBusy("");
      setPhotos(photos.map((p) => p.caption ? p : { ...p, caption: showing === "view" ? "Interior, viewed toward the rear wall" : "Looking west from the parking area" }));
    }, 1400);
  }

  return (
    <div onDragOver={(e) => { e.preventDefault(); if (from.current === null) setDragging(true); }}
         onDragLeave={(e) => { if (e.currentTarget === e.target) setDragging(false); }}
         onDrop={(e) => { e.preventDefault(); setDragging(false); if (from.current === null) setPhotos(window.DEMO.photos); }}>
      <ScreenHead title="Photos"
        sub={`${photos.length} ${photos.length === 1 ? "photo" : "photos"}, about ${pages} ${pages === 1 ? "page" : "pages"}. Drag a photo to reorder it.`}
        actions={
          <>
            <Button size="sm" disabled={!!busy || photos.length === 0}
              onClick={() => { setBusy("Building photo pages…"); setDone(null);
                setTimeout(() => { setBusy(""); setDone("Photo Pages.docx"); }, 1200); }}>
              Build photo pages
            </Button>
            <Button size="sm" variant="secondary" disabled={!!busy || photos.length === 0} onClick={openChooser}>
              Suggest captions
            </Button>
            <LinkButton onClick={() => setPhotos(window.DEMO.photos)}>Add photos</LinkButton>
          </>
        }
        below={busy ? <Working label={busy} /> : null} />

      {done ? (
        <div style={{ marginBottom: "var(--space-4)" }}>
          <Banner tone="done">Done. <strong>{done}</strong> was created in this job's Photos folder. Nothing was overwritten.</Banner>
        </div>
      ) : null}

      {photos.length === 0 ? (
        <DropZone onFiles={() => setPhotos(window.DEMO.photos)} onClick={() => setPhotos(window.DEMO.photos)}>
          <strong>Drag photos here</strong> or use Add photos. They are copied into this job's Photos
          folder and your originals stay untouched.
        </DropZone>
      ) : (
        <PhotoGrid>
          {photos.map((p, i) => (
            <PhotoTile key={p.file + i} src={p.src} alt={p.file} caption={p.caption}
              onCaption={(c) => setCaption(i, c)} draggable
              dragProps={{
                onDragStart: () => (from.current = i),
                onDragOver: (e) => e.preventDefault(),
                onDragEnd: () => (from.current = null),
                onDrop: (e) => { e.stopPropagation(); reorder(i); },
              }} />
          ))}
        </PhotoGrid>
      )}

      {dragging && photos.length > 0 ? <DragHint>Drop to add these photos to the job</DragHint> : null}

      {asking ? (
        <Sheet title="How should the captions read?" onClose={() => setAsking(false)}
          sub="Your own photos, written both ways. This is how the printed page is laid out."
          foot={
            <>
              <p className="rrf-sheet__keep">Captions you have already typed are never changed.</p>
              <Button onClick={runCaptions} disabled={previewing}>Use this style</Button>
              <LinkButton onClick={() => setAsking(false)}>Cancel</LinkButton>
            </>
          }>
          <PagePreview
            head={<SegmentedControl value={showing} onChange={setShowing}
              options={styles.map((s) => ({ key: s.key, label: s.label, flag: s.key === "view" ? "suggested" : undefined }))} />}
            waiting={previewing}
            waitingNote={<><div className="rrf-sweep"><span /></div><p>Writing sample captions for three of your photos.<br />This takes a few seconds.</p></>}
            rows={(photos.length ? photos : window.DEMO.photos).slice(0, 3).map((p, i) => ({
              src: p.src,
              caption: SAMPLES[showing][i],
            }))} />
        </Sheet>
      ) : null}
    </div>
  );
}
Object.assign(window, { PhotosScreen });
