import React, { useEffect, useState } from "react";
import JobsPortal from "./screens/JobsPortal.jsx";
import JobHome from "./screens/JobHome.jsx";
import PhotosScreen from "./screens/PhotosScreen.jsx";
import SectionPicker from "./screens/SectionPicker.jsx";
import Settings from "./screens/Settings.jsx";
import NewJob from "./screens/NewJob.jsx";
import ChooseFolder from "./screens/ChooseFolder.jsx";
import ActiveJobs from "./screens/ActiveJobs.jsx";
import UpdateStep from "./screens/UpdateStep.jsx";
import { getWorkspace, getDemo, resetDemo, appVersion, listJobs, updateStatus } from "./api.js";

const TRAIL = { photos: "Photos", sections: "Sections" };

// Where he was, so a browser refresh does not throw away his place. The app
// has no addresses of its own: every screen lives at "/" and the view is
// state, so a refresh took him back to Jobs from wherever he was working.
//
// Deliberately not routing. Giving each screen a real address is a larger
// change than this pass was asked for, and it is written up rather than
// started. This is the small version: remember the last screen for this tab
// only, and never restore one that is not still there.
const WHERE = "rrf.where";

function remember(view) {
  try { sessionStorage.setItem(WHERE, JSON.stringify(view)); } catch { /* private mode */ }
}

function lastPlace() {
  try {
    const found = JSON.parse(sessionStorage.getItem(WHERE) || "null");
    // Only the three screens that belong to a job. Setup screens and the
    // folder chooser are steps, and dropping back into a step out of context
    // would be worse than starting at Jobs.
    if (found && ["job", "photos", "sections"].includes(found.screen) && found.job) {
      return found;
    }
  } catch { /* damaged or unavailable: start at Jobs, which always works */ }
  return null;
}

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
  // What the startup look found, and whether he has opened the step.
  // Nothing here goes to the network: the look already happened, in the
  // background, when the app started.
  const [update, setUpdate] = useState(null);
  const [updating, setUpdating] = useState(false);

  // Two different failures, and they used to read the same. A damaged
  // settings file is not an unreachable server, and telling Mark to restart
  // the app would send him round a loop that cannot fix it. The server flags
  // that one case; everything else, including a fetch that never got an
  // answer, keeps the message it has always had. Only the flagged case shows
  // the server's own sentence, so this is not a rule that puts any backend
  // text on the startup screen.
  const CANNOT_REACH = "Could not reach the app's server. Close this tab and start the app again.";

  // Remembered on every move, so nothing has to call a second function to
  // keep the two in step.
  useEffect(() => { remember(view); }, [view]);

  useEffect(() => {
    getWorkspace().then((saved) => {
      setWs(saved);
      // Put him back only if the job is still one he is working on. A folder
      // renamed or made inactive since he last looked would otherwise open a
      // screen for something that is not there.
      const back = saved && saved.valid ? lastPlace() : null;
      if (back) {
        listJobs()
          .then((live) => {
            if (live.some((one) => one.name === back.job)) setView(back);
          })
          .catch(() => { /* Jobs is the safe place to be */ });
      }
    })
      .catch((e) => setWsError(
        e && e.status === 409 && e.stateUnreadable && e.message ? e.message : CANNOT_REACH));
    getDemo().then(setDemo).catch(() => {});
    // Shown on every screen, because the masthead is on every screen. It is
    // how Spenser tells which installed folder he actually launched.
    appVersion().then((v) => setVersion(v.version || "")).catch(() => {});
    // The masthead is on every screen, so the notice is too. A bucket that is
    // down, no internet, or a development checkout all answer the same way and
    // nothing renders.
    updateStatus().then(setUpdate).catch(() => {});
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

  const offered = !!(update && update.available);

  const updateStep = updating && (
    <UpdateStep version={version} available={update.available} size={update.size}
                onClose={() => setUpdating(false)} />
  );

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
      {version && !offered && (
        <span className="version" title="Installed version">v{version}</span>
      )}
      {/* Quiet until there is something to say. A click leads to a step: the
          question about whether to update is asked inside the action. */}
      {offered && (
        <button className="version version-update" onClick={() => setUpdating(true)}
                title={`You are on version ${version}`}>
          Update available
        </button>
      )}
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
          {updateStep}{resetStep}{resetNote}
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
          {updateStep}{resetStep}{resetNote}
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
        {updateStep}{resetStep}{resetNote}
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
          <Settings workspace={ws} version={version}
                    onChangeFolder={() => setView({ screen: "choose", job: null })}
                    onWorkspaceChanged={(saved) => { setWs(saved); toJobs(); }} />
        )}
      </div>
    </>
  );
}
