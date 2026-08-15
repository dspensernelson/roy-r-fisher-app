const { ScreenHead, RoadCard, Panel, Field, Button, LinkButton, Banner, Working } = window.RoyRFisherDesignSystem_5d521b;

const BLANK = { street: "", city: "", state: "Iowa", property_type: "", engagement: "",
  client: "", intended_use: "", effective_date: "", due_date: "", file_number: "" };

function NewJobScreen({ onCreated, onCancel }) {
  const [road, setRoad] = React.useState(null);
  const [form, setForm] = React.useState(BLANK);
  const [name, setName] = React.useState("");
  const [edited, setEdited] = React.useState(false);
  const [busy, setBusy] = React.useState("");
  const set = (k) => (v) => setForm({ ...form, [k]: v });

  React.useEffect(() => {
    if (edited) return;
    const { city, street, engagement, effective_date } = form;
    if (!city.trim() || !street.trim() || !engagement) return;
    const year = (effective_date.match(/\b(20\d\d)\b/) || [])[1];
    const tail = engagement === "Tax appeal" ? ` - ${year || "2026"} Tax` : year ? ` - ${year}` : "";
    setName(`${city.toUpperCase()}_${street}${tail}`);
  }, [form, edited]);

  const ready = form.street.trim() && form.city.trim() && form.property_type && form.engagement && name.trim();

  if (!road) return (
    <>
      <ScreenHead title="New job" sub="Two ways to start. Both end at the same form, and you check every line before anything is made." />
      <div className="rrf-roads">
        <RoadCard title="Type it in" onClick={() => setRoad("type")}
          body="The address, what kind of property it is, and what kind of appraisal. About a minute." />
        <RoadCard title="Read the engagement letter" soon onClick={() => setRoad("letter")}
          body="Drop the signed letter and the app fills in what it can find. You check it before anything is saved." />
      </div>
      <div style={{ marginTop: "var(--space-5)" }}><LinkButton size="body" onClick={onCancel}>Cancel</LinkButton></div>
    </>
  );

  return (
    <>
      <ScreenHead stack title="New job" sub="Nothing is made until you press the button at the bottom." />
      {road === "letter" ? (
        <div style={{ maxWidth: 720, marginBottom: "var(--space-4)" }}>
          <Banner tone="warn">Reading a letter is not built yet. Fill this in and everything else works the same.</Banner>
        </div>
      ) : null}
      <Panel label="Needed to start">
        <div className="rrf-fields">
          <Field label="Street address" value={form.street} onChange={set("street")} placeholder="4151 4th St SW" autoFocus />
          <Field label="City" value={form.city} onChange={set("city")} placeholder="Mason City" />
          <Field label="State" value={form.state} onChange={set("state")} />
          <Field label="Kind of property" options={window.DEMO.types} value={form.property_type} onChange={set("property_type")} />
          <Field label="Kind of appraisal" options={window.DEMO.engagements} value={form.engagement} onChange={set("engagement")} />
        </div>
      </Panel>
      <Panel label="Can wait" note="The fee is not recorded here. The job points at the engagement letter instead.">
        <div className="rrf-fields">
          <Field label="Client" value={form.client} onChange={set("client")} />
          <Field label="Intended use" value={form.intended_use} onChange={set("intended_use")} />
          <Field label="Effective date of value" value={form.effective_date} onChange={set("effective_date")} placeholder="January 1, 2026" />
          <Field label="Report due date" value={form.due_date} onChange={set("due_date")} placeholder="June 15, 2026" />
          <Field label="Office file number" value={form.file_number} onChange={set("file_number")} />
        </div>
      </Panel>
      <Panel label="Folder name">
        <Field derived value={name} onChange={(v) => { setName(v); setEdited(true); }}
          placeholder="Fill in the address and this fills itself in"
          hint="This is the folder that gets made, in your usual style. Edit it if you want it named differently." />
      </Panel>
      <div className="rrf-actionrow">
        <Button disabled={!ready || !!busy} onClick={() => { setBusy("Making the folders…");
          setTimeout(() => { setBusy(""); onCreated({ name, photos: 0, engagement: form.engagement, type: form.property_type }); }, 900); }}>
          Make the job
        </Button>
        <LinkButton onClick={onCancel}>Cancel</LinkButton>
        {busy ? <Working label={busy} /> : null}
      </div>
    </>
  );
}
Object.assign(window, { NewJobScreen });
