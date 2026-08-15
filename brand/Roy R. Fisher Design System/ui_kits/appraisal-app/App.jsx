const { AppShell } = window.RoyRFisherDesignSystem_5d521b;
const TAIL = { photos: "Photos", sections: "Sections", settings: "Settings" };

function App() {
  const [view, setView] = React.useState({ screen: "jobs", job: null });
  const [sections, setSections] = React.useState([]);
  const job = view.job;

  const trail = [{ label: "Jobs", onClick: () => setView({ screen: "jobs", job: null }) }];
  if (job) trail.push({ label: job.name, onClick: () => setView({ screen: "job", job }) });
  if (TAIL[view.screen] && view.screen !== "settings") trail.push({ label: TAIL[view.screen] });

  const go = (screen, j = job) => setView({ screen, job: j });

  return (
    <AppShell markSrc="../../assets/logo/rrf-mark.svg" trail={trail}
      crumbRight={<button className="rrf-crumb" aria-current={view.screen === "settings" ? "page" : undefined}
        onClick={() => setView({ screen: "settings", job: null })}>Settings</button>}>
      {view.screen === "jobs" ? (
        <JobsScreen onOpen={(j) => { setSections(window.DEMO.sections.filter((s) => s !== "Cost Approach")); go("job", j); }}
          onNew={() => go("new", null)} />
      ) : null}
      {view.screen === "new" ? (
        <NewJobScreen onCancel={() => go("jobs", null)}
          onCreated={(j) => { setSections([]); setView({ screen: "sections", job: j }); }} />
      ) : null}
      {view.screen === "job" ? (
        <JobScreen job={job} sections={window.DEMO.reportRows} tasks={window.DEMO.tasks}
          arrived={window.DEMO.arrived} onOpenPhotos={() => go("photos")} onEditSections={() => go("sections")} />
      ) : null}
      {view.screen === "sections" ? (
        <SectionsScreen job={job} sections={sections} onSave={(s) => { setSections(s); go("job"); }} />
      ) : null}
      {view.screen === "photos" ? <PhotosScreen job={job} /> : null}
      {view.screen === "settings" ? <SettingsScreen /> : null}
    </AppShell>
  );
}
ReactDOM.createRoot(document.getElementById("root")).render(<App />);
