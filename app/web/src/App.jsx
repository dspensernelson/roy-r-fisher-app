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
import CloseX from "./CloseX.jsx";
import { getWorkspace, getDemo, resetDemo, appVersion, listJobs, updateStatus, closeTheApp } from "./api.js";

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
  // F13. Closing the app is a question and then a result, and both are
  // windows over whatever screen he is on, because the button that starts it
  // lives in the nav bar and the nav bar is on every screen. Press it while
  // looking at a job's photographs and it has to ask there.
  const [askClose, setAskClose] = useState(false);
  const [closed, setClosed] = useState(false);

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
    refreshUpdate();
  }, []);

  // Asked again whenever something might have changed the answer, not only at
  // load. `Check now` on Settings updates what the server remembers, and until
  // 2026-09-03 nothing told the masthead to look again: the notice still held
  // the answer from before the newer version existed, so it told Spenser to
  // press a button that was not on the screen.
  function refreshUpdate() {
    return updateStatus().then(setUpdate).catch(() => {});
  }

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
  // The one way into the update step. The masthead button and the button
  // beside Check now on Settings both press this, so they cannot drift.
  const openUpdate = () => setUpdating(true);

  const updateStep = updating && (
    <UpdateStep version={version} available={update.available} size={update.size}
                onClose={() => setUpdating(false)} />
  );

  // The band and the mark travel together, inside one constant, because the
  // masthead is rendered from five places below and a band added at each of
  // them is a band that will one day be missing from one of them.
  const masthead = (
    <>
    <div className="topline" />
    <header className="masthead">
      {/* The firm's mark: three columns with an angled cut on the taller
          centre one. These points are traced from the logo files by measuring
          the raster's own pixel edges, and the colours are written out rather
          than taken from the tokens, so that changing a token can never
          redraw the mark. The three plain bars this replaces were drawn from
          memory, in a red the firm does not use, with no cut at all. */}
      <svg width="15" height="40" viewBox="0 0 80 215" role="img"
           aria-label="Roy R. Fisher">
        <polygon fill="#231F20" points="21,55 21,195 1,195 1,77" />
        <polygon fill="#8C0C04" points="54,2 54,214 26,214 26,26" />
        <polygon fill="#231F20" points="59,55 79,76 79,195 59,195" />
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
        <button className="version version-update" onClick={openUpdate}
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
    </>
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
        <button className="button final" onClick={runReset}>Reset demo</button>
        <button className="linky" onClick={() => setAsking(false)}>Cancel</button>
      </div>
    </div>
  );

  // Built from the window values already in the stylesheet rather than as a
  // second kind of window: the same `.sheet` the photographs screen asks its
  // questions in.
  const closeStep = (askClose || closed) && (
    <div className="sheet-back"
         onClick={(e) => { if (!closed && e.target === e.currentTarget) setAskClose(false); }}>
      {closed ? (
        /* No Cancel. By the time this is up the decision is made and the
           server is gone, so there is nothing to back out to and nothing
           left to press. B10 is answered behind it, not in these words. */
        <div className="sheet" role="status" aria-label="Closing now">
          <h2>Closing now.</h2>
          <p className="fine">
            You can close this tab. Start the app again with the Roy R. Fisher
            icon on your Desktop.
          </p>
        </div>
      ) : (
        <div className="sheet" role="dialog" aria-modal="true" aria-label="Close the app?">
          {/* The question and nothing else. It used to carry a line saying
              that closing the browser tab does not stop the app and this
              does, which explains why the button exists to somebody whose
              finger is already on it. Spenser, 2026-09-15: "that is a weird
              place for that comment". */}
          <h2>Close the app?</h2>
          <div className="sheet-acts">
            <button className="linky" onClick={() => setAskClose(false)}>Cancel</button>
            <button className="button final" onClick={async () => {
              setAskClose(false); setClosed(true);
              try { await closeTheApp(); } catch { /* it is going away */ }
            }}>
              Close the app
            </button>
          </div>
        </div>
      )}
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
      {resetError && (
        <div className="error">
          <CloseX onClose={() => setResetError(null)} what="this message" />
          {resetError}
        </div>
      )}
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

  // Inside a job, the first crumb stops being a word and becomes a way out.
  // Spenser, 2026-09-04: *"there should be a Back to Jobs at the very top. We
  // need to make it obvious these are not computer people."* A crumb trail is
  // a thing computer people read. On the jobs screen it stays a plain word,
  // because he is already there.
  const inside = !!view.job || view.screen === "settings";
  const crumbs = [
    <button key="jobs" className={inside ? "crumb-chip" : ""}
            onClick={() => setView({ screen: "jobs", job: null })}>
      {inside ? "\u2039 Back to Jobs" : "Jobs"}
    </button>,
  ];
  // The job's own name is a chip too. On the photographs screen it is the
  // crumb he needs most, and it was plain white text that did nothing until
  // the pointer was on it.
  if (view.job) crumbs.push(<span key="s1">›</span>,
    <button key="job" className="crumb-chip"
            onClick={() => setView({ screen: "job", job: view.job })}>{view.job}</button>);
  if (TRAIL[view.screen]) crumbs.push(<span key="s2">›</span>, <span key="tail">{TRAIL[view.screen]}</span>);

  const toJobs = () => setView({ screen: "jobs", job: null });

  return (
    <div className={closed ? "shell finished" : "shell"}>
      <div id="alive">
      {masthead}
      <div className="bar">
        <nav className="bar-inner">
          {crumbs}
          {/* The job comes with him. Settings used to drop it, so the only
              way back into the job he was working on was Jobs and then
              opening it again. Nothing on Settings is about a job, so
              carrying it changes nothing except the way back. */}
          <button className={`bar-right ${view.screen === "settings" ? "here" : ""}`}
                  onClick={() => setView({ screen: "settings", job: view.job })}>
            Settings
          </button>
          {/* F13.3: a solid red box, not a link, so it reads differently from
              the crumbs and `Settings` beside it. The only filled thing in
              the bar. Disabled once the app has actually gone, with
              everything else. */}
          <button className="bar-close" disabled={closed}
                  onClick={() => setAskClose(true)}>
            Close the app
          </button>
        </nav>
      </div>
      {/* Marked while the photographs screen is in it, which draws that screen
          at 90 per cent of its design sizes. See `.frame.is-photos`. */}
      <div className={`frame${view.screen === "photos" ? " is-photos" : ""}`}>
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
                    onWorkspaceChanged={(saved) => { setWs(saved); toJobs(); }}
                    onUpdateChecked={refreshUpdate}
                    onUpdate={offered ? openUpdate : undefined} />
        )}
      </div>
      </div>
      {closeStep}
    </div>
  );
}
