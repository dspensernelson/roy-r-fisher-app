const { ScreenHead, Bands, BandHead, Worklist, TaskRow, Progress, SectionRow, LinkButton } = window.RoyRFisherDesignSystem_5d521b;
const SPRITE = "../../assets/icons/sprite.svg";

/* The job screen is a worklist, not a comparison: one ordered set of things to
   do — what he can act on now, without waiting on anyone — with the report's
   sections alongside. Nothing here claims who is holding something up; the app
   reads folders, and that is all it knows. Things he cannot do yet say so on
   the section rows, which is the only place they live. */
function JobScreen({ job, sections, tasks, arrived, onOpenPhotos, onEditSections }) {
  const ready = sections.filter((s) => !s.needs).length;
  return (
    <>
      <ScreenHead title={job.name} sub={`${job.type} · ${job.engagement}${job.due ? " · due " + job.due : ""}`}
        actions={
          <>
            <button className="rrf-btn rrf-btn--primary rrf-btn--sm" onClick={onOpenPhotos}>Build photo pages</button>
            <LinkButton onClick={onEditSections}>Change sections</LinkButton>
          </>
        }
        below={sections.length ? <Progress ready={ready} total={sections.length} /> : null} />
      <Bands
        left={
          <>
            <Worklist title="You can do these now">
              {tasks.map((t, i) => (
                <TaskRow key={t.name} {...t} sprite={SPRITE} next={i === 0}
                  onClick={t.go === "photos" ? onOpenPhotos : t.go === "sections" ? onEditSections : undefined} />
              ))}
            </Worklist>
            <Worklist title="Already here">
              {arrived.map((a) => <TaskRow key={a.name} tone="done" sprite={SPRITE} {...a} />)}
            </Worklist>
          </>
        }
        right={
          <>
            <BandHead title="The report" note={`${sections.length} sections, in print order`}
              action={<LinkButton onClick={onEditSections}>Change</LinkButton>} />
            {sections.map((s, i) => (
              <SectionRow key={s.name} num={i + 1} name={s.name} state={s.needs || s.has || s.note}
                stateTone={s.needs ? "needs" : s.has ? "has" : undefined}
                live={s.live} onClick={s.live ? onOpenPhotos : undefined} />
            ))}
          </>
        } />
    </>
  );
}
Object.assign(window, { JobScreen });
