import React, { useEffect, useState } from "react";
import JobsPortal from "./screens/JobsPortal.jsx";
import JobHome from "./screens/JobHome.jsx";
import PhotosScreen from "./screens/PhotosScreen.jsx";
import SectionPicker from "./screens/SectionPicker.jsx";
import Settings from "./screens/Settings.jsx";
import NewJob from "./screens/NewJob.jsx";
import ChooseFolder from "./screens/ChooseFolder.jsx";
import ActiveJobs from "./screens/ActiveJobs.jsx";
import { getWorkspace, getDemo, resetDemo, appVersion } from "./api.js";

const TRAIL = { photos: "Photos", sections: "Sections" };

export default function App() {
  const [view, setView] = useState({ screen: "jobs", job: null });
  const [ws, setWs] = useState(null);
  const [demo, setDemo] = useState({ demo_mode: false });
  const [setup, setSetup] = useState(false);   // choosing active jobs, first time
  const [asking, setAsking] = useState(false); // the reset confirmation
  const [resetting, setResetting] = useState("");
  const [resetError, setResetError] = useState("");
  const [wsError, setWsError] = useState("");
  const [version, setVersion] = useState("");

  // Two different failures, and they used to read the same. A damaged
  // settings file is not an unreachable server, and telling Mark to restart
  // the app would send him round a loop that cannot fix it. The server flags
  // that one case; everything else, including a fetch that never got an
  // answer, keeps the message it has always had. Only the flagged case shows
  // the server's own sentence, so this is not a rule that puts any backend
  // text on the startup screen.
  const CANNOT_REACH = "Could not reach the app's server. Close this tab and start the app again.";

  useEffect(() => {
    getWorkspace().then(setWs)
      .catch((e) => setWsError(
        e && e.status === 409 && e.stateUnreadable && e.message ? e.message : CANNOT_REACH));
    getDemo().then(setDemo).catch(() => {});
    // Shown on every screen, because the masthead is on every screen. It is
    // how Spenser tells which installed folder he actually launched.
    appVersion().then((v) => setVersion(v.version || "")).catch(() => {});
  }, []);

  async function runReset() {
    setAsking(false); setResetting("Putting the demo jobs back..."); setResetError("");
    try {
      await resetDemo();
      const fresh = await getWorkspace();
      setWs(fresh); setSetup(false); setView({ screen: "jobs", job: null });
    } catch (e) { setResetError(e.message); }
    setResetting("");
  }

  const masthead = (
    <header className="masthead">
      <svg width="30" height="40" viewBox="0 0 30 40" aria-hidden="true">
        <rect x="2" y="12" width="6" height="28" fill="#782028" />
        <rect x="10" y="2" width="7" height="38" fill="#782028" />
        <rect x="19" y="8" width="6" height="32" fill="#343538" />
      </svg>
      <div>
        <div className="wordmark">ROY R. FISHER</div>
        <div className="tagline">“The Established Commercial Valuation Experts”</div>
      </div>
      {/* Only ever here when this computer is explicitly set up for testing.
          Mark's install has no demo configuration, so it never renders. */}
      {version && <span className="version" title="Installed version">v{version}</span>}
      {demo.demo_mode && (
        <button className="reset-demo" onClick={() => setAsking(true)} disabled={!!resetting}>
          {resetting ? "Resetting..." : "Reset demo"}
        </button>
      )}
    </header>
  );

  const resetStep = asking && (
    <div className="confirm" style={{ margin: "20px 0" }}>
      <p style={{ margin: "0 0 10px" }}><strong>Put the demo jobs back to the clean baseline?</strong></p>
      <p className="setting-fine" style={{ margin: "0 0 12px" }}>
        This forgets the jobs folder and every active job, and replaces the demo job
        folders with the baseline copy. Captions, built Word files, thumbnails and
        anything added during this test run go with it. Your Anthropic key is not
        touched, and nothing outside the demo folder is either.
      </p>
      <div className="setting-actions">
        <button className="button" onClick={runReset}>Reset demo</button>
        <button className="linky" onClick={() => setAsking(false)}>Cancel</button>
      </div>
    </div>
  );

  const resetNote = (
    <>
      {resetting && (
        <div className="working" style={{ margin: "16px 0" }}>
          <span className="loading-bar"><span /></span>
          <span className="working-text">{resetting}</span>
        </div>
      )}
      {resetError && <div className="error">{resetError}</div>}
    </>
  );

  if (wsError) return (<>{masthead}<div className="frame"><div className="error">{wsError}</div></div></>);
  if (!ws) return (<>{masthead}<div className="frame"><p className="sub">Loading...</p></div></>);

  // Nothing usable to point at. One screen, one question, and no navigation
  // to places that cannot work yet.
  if (!ws.valid) {
    return (
      <>
        {masthead}
        <div className="frame">
          {resetStep}{resetNote}
          <ChooseFolder first missing={ws.chosen ? ws.path : ""}
                        onSaved={(saved) => { setWs(saved); setSetup(true); }} />
        </div>
      </>
    );
  }

  // Straight from choosing the folder into choosing which jobs are live.
  if (setup) {
    return (
      <>
        {masthead}
        <div className="frame">
          {resetStep}{resetNote}
          <ActiveJobs first onDone={() => { setSetup(false); setView({ screen: "jobs", job: null }); }} />
        </div>
      </>
    );
  }

  const crumbs = [
    <button key="jobs" onClick={() => setView({ screen: "jobs", job: null })}>Jobs</button>,
  ];
  if (view.job) crumbs.push(<span key="s1">›</span>,
    <button key="job" onClick={() => setView({ screen: "job", job: view.job })}>{view.job}</button>);
  if (TRAIL[view.screen]) crumbs.push(<span key="s2">›</span>, <span key="tail">{TRAIL[view.screen]}</span>);

  const toJobs = () => setView({ screen: "jobs", job: null });

  return (
    <>
      {masthead}
      <div className="bar">
        <nav className="bar-inner">
          {crumbs}
          <button className={`bar-right ${view.screen === "settings" ? "here" : ""}`}
                  onClick={() => setView({ screen: "settings", job: null })}>
            Settings
          </button>
        </nav>
      </div>
      <div className="frame">
        {resetStep}{resetNote}
        {view.screen === "jobs" && <JobsPortal onOpen={(job) => setView({ screen: "job", job })}
                                            onNew={() => setView({ screen: "new", job: null })}
                                            onManage={() => setView({ screen: "active", job: null })}
                                            onChangeFolder={() => setView({ screen: "choose", job: null })} />}
        {view.screen === "active" && <ActiveJobs onDone={toJobs} onCancel={toJobs} />}
        {view.screen === "choose" && (
          <ChooseFolder current={ws.path}
                        onSaved={(saved) => { setWs(saved); setSetup(true); }}
                        onCancel={toJobs} />
        )}
        {view.screen === "new" && (
          <NewJob onCreated={(job) => setView({ screen: "sections", job })} onCancel={toJobs} />
        )}
        {view.screen === "job" && (
          <JobHome job={view.job}
                   onOpenPhotos={() => setView({ screen: "photos", job: view.job })}
                   onEditSections={() => setView({ screen: "sections", job: view.job })} />
        )}
        {view.screen === "sections" && (
          <SectionPicker job={view.job} onDone={() => setView({ screen: "job", job: view.job })} />
        )}
        {view.screen === "photos" && <PhotosScreen job={view.job} />}
        {view.screen === "settings" && (
          <Settings workspace={ws}
                    onChangeFolder={() => setView({ screen: "choose", job: null })}
                    onWorkspaceChanged={(saved) => { setWs(saved); toJobs(); }} />
        )}
      </div>
    </>
  );
}
