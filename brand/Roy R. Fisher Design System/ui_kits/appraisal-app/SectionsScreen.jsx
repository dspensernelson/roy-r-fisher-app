const { ScreenHead, Panel, Checklist, Button, Banner, Working } = window.RoyRFisherDesignSystem_5d521b;

function SectionsScreen({ job, sections, onSave }) {
  const all = window.DEMO.sections;
  const [picked, setPicked] = React.useState(() =>
    Object.fromEntries(all.map((s) => [s, sections.length ? sections.includes(s) : !["Cost Approach", "Addenda"].includes(s)])));
  const [busy, setBusy] = React.useState("");
  const count = Object.values(picked).filter(Boolean).length;
  const thin = job.engagement === "Restricted short form" || job.engagement === "Rent study";

  return (
    <>
      <ScreenHead title="Sections in this report"
        sub={`A ${job.engagement.toLowerCase()} usually runs these. Uncheck anything this one does not need.`} />
      {thin ? (
        <div style={{ maxWidth: 720, marginBottom: "var(--space-4)" }}>
          <Banner tone="warn">We have only one finished report of this kind on file, so this list is a starting point rather than the firm's standard. Check it carefully.</Banner>
        </div>
      ) : null}
      <Panel>
        <Checklist items={all} checked={picked} onToggle={(n, v) => setPicked({ ...picked, [n]: v })} />
      </Panel>
      <div className="rrf-actionrow">
        <Button disabled={!!busy} onClick={() => { setBusy("Saving…");
          setTimeout(() => { setBusy(""); onSave(all.filter((s) => picked[s])); }, 700); }}>
          Save these sections
        </Button>
        {busy ? <Working label={busy} /> : <span style={{ fontSize: "var(--text-body)", color: "var(--text-secondary)" }}>{count} {count === 1 ? "section" : "sections"} checked</span>}
      </div>
    </>
  );
}
Object.assign(window, { SectionsScreen });
