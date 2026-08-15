const { ScreenHead, SettingCard, Lamp, Field, Button, LinkButton, Banner, Working } = window.RoyRFisherDesignSystem_5d521b;

function SettingsScreen() {
  const [keySet, setKeySet] = React.useState(false);
  const [typed, setTyped] = React.useState("");
  const [busy, setBusy] = React.useState("");
  const [note, setNote] = React.useState(null);
  const [replacing, setReplacing] = React.useState(false);
  const asking = !keySet || replacing;

  function save() {
    setBusy("Checking the key…");
    setTimeout(() => { setBusy(""); setKeySet(true); setReplacing(false); setTyped("");
      setNote("The key works. Writing captions is on."); }, 900);
  }
  return (
    <>
      <ScreenHead title="Settings" sub="Set this up once. The app remembers it on this computer." />
      <SettingCard title="Writing captions and reading letters" lamp={<Lamp state={busy ? "busy" : keySet ? "on" : "off"} />}
        fine="Your key is kept in a file in your own user folder, outside this program, and it is never shown on screen again or written into any job.">
        <p className="rrf-settingcard__body">
          Two things need a key from Anthropic: writing photo captions for you, and reading a signed
          engagement letter to fill in a new job. Everything else in the app works the same either way,
          and you can always type captions in yourself.
        </p>
        {keySet && !replacing ? (
          <>
            <p className="rrf-settingcard__body">A key is saved on this computer. It ends in <strong>4Kq2</strong>.</p>
            <div className="rrf-actionrow">
              <Button variant="quiet" onClick={() => { setReplacing(true); setNote(null); }}>Replace it</Button>
              <LinkButton size="body" onClick={() => { setKeySet(false); setNote("The key was removed."); }}>Remove it</LinkButton>
            </div>
          </>
        ) : null}
        {asking ? (
          <>
            <div style={{ maxWidth: 520, marginBottom: "var(--space-3)" }}>
              <Field mono type="password" label="Paste your key" value={typed}
                onChange={setTyped} placeholder="Paste it here" />
            </div>
            <div className="rrf-actionrow">
              <Button onClick={save} disabled={!typed.trim() || !!busy}>Check and save</Button>
              {replacing ? <LinkButton onClick={() => { setReplacing(false); setTyped(""); }}>Cancel</LinkButton> : null}
              {busy ? <Working label={busy} /> : null}
            </div>
            <p className="rrf-settingcard__body" style={{ marginTop: "var(--space-4)" }}>
              You get a key from <strong>console.anthropic.com</strong>, under Settings, then Keys. It is a
              long line of characters starting with <strong>sk-ant-</strong>. Copy the whole thing.
            </p>
          </>
        ) : null}
        {note ? <Banner tone="done">{note}</Banner> : null}
      </SettingCard>
    </>
  );
}
Object.assign(window, { SettingsScreen });
