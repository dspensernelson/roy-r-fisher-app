# Now

**The one page that says where we are.** Read it first, every session. Update it
the moment anything on it changes, not at the end.

Everything here is a pointer. The detail lives in `docs/BUGS.md`,
`docs/PUNCHLIST.md`, `docs/THE-WALK-2026-09-04.md` and `docs/CHECKS.md`.

Last updated 2026-09-15.

---

## The goal

**Get a version to Mark's office.** They run 0.6.9. Nothing has been uploaded
to them since 2026-09-07. Every other item on this page is either serving that
or is a detour from it.

## Doing now

- [ ] **Find out why 0.7.5 dies on startup.** It installs, starts, and dies
      before serving anything. A race between the launcher's background threads
      and its first import was proposed and **not confirmed**: Spenser ran the
      test five times on 2026-09-15 and all five passed. Unexplained.

## Blocked behind that

- [ ] **An update Spenser can take himself**, the way Colleen does. His machine
      now reads a channel on his Mac, `RRF_UPDATE_BUCKET` pointed at
      `http://192.168.64.1:8088`. The button appeared and worked. The version it
      installed did not start.
- [ ] **Anything reaching the office.** No upload until an update is proven.

## Waiting on Spenser

- [ ] **The Cloudflare setup** for `Send the log to Spenser`. Until it is done
      the button says so plainly rather than failing. Steps are in the header of
      `tools/worker/send-the-log.js`.
- [ ] **How far back the log goes.** Punch list.
- [ ] **What Reset puts back.** Punch list.
- [ ] **Which job produced the 700 KB photographs.** Punch list. Nobody can look
      until he names it.
- [ ] **The black window after an update.** Punch list. Three shapes proposed,
      none chosen.

## Outstanding, counted

- **14 bugs** in `docs/BUGS.md`.
- **5 items** from his 2026-09-04 walk never built, all on the job screen and
  the update screen. `docs/THE-WALK-2026-09-04.md`.
- **28 by-hand checks** exist. **The last full run was 0.6.6 on 2026-09-04.**
  Nothing since has been checked on Windows in any organised way. That is the
  largest single gap on this page.
- **The launcher swallows errors.** It speaks for two named failures and throws
  everything else away, because the shortcut runs `pythonw.exe` with nowhere to
  print. This is what hid the 0.7.5 crash for an hour.

## Settled today, so nobody reopens it

- The photographs screen, rebuilt to a design he approved after eight rounds.
  Saved at `docs/design/photos-screen.html`.
- Settings, in two columns, in the order he chose.
- `Close the app` in the nav bar, asking in a window over any screen.
- The five kinds, the three-words rule, the lower-right rule, and the
  firing-rate rule, all in `HOW-WE-WORK.md`.
- Version numbering: **four numbers for his test builds** (0.7.5.1), **three for
  the office** (0.7.6). Letters break the update check and are forbidden; see
  the note in `HOW-WE-WORK.md`.

---

**The rule for this file.** One thing at a time under "Doing now". Anything he
asks for goes on this page when he asks for it, not when it is convenient. If
it is not written here it will be forgotten, which is the lesson of
2026-09-14 and the reason `docs/THE-WALK-2026-09-04.md` exists.
