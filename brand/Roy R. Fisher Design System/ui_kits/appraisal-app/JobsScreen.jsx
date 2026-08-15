const { ScreenHead, JobCard, NewJobCard, Banner } = window.RoyRFisherDesignSystem_5d521b;

function JobsScreen({ onOpen, onNew }) {
  const split = (name) => { const i = name.indexOf("_"); return i > 0 ? [name.slice(0, i), name.slice(i + 1)] : ["", name]; };
  return (
    <>
      <ScreenHead title="Jobs" sub="Every job folder you have, and the next thing each one needs." />
      <div className="rrf-cards">
        {window.DEMO.jobs.map((j) => {
          const [city, addr] = split(j.name);
          return <JobCard key={j.name} city={city} address={addr}
            meta={`${j.photos} photos · ${j.engagement}`}
            next={{ ...j.next, sprite: "../../assets/icons/sprite.svg" }}
            ready={j.ready} total={j.total} onClick={() => onOpen(j)} />;
        })}
        <NewJobCard onClick={onNew} />
      </div>
    </>
  );
}
Object.assign(window, { JobsScreen });
