# Plan: Mark presses a button and the app updates itself

Branch: `in-app-update`, cut from `bulk-classify` on 2026-08-28.

This plan destroys itself. Its last task folds what was learned into
`docs/ROADMAP.md` and deletes this file. `test_plans_delete_themselves.py`
enforces that, and this plan uses task checkboxes so the test can see it. The
pilot plan uses COMPLETE headings instead and the test is blind to it; this one
is not.

## Read first

1. `HOW-WE-WORK.md`. It governs. Its Never list has no judgement in it.
2. `README.md`.
3. `docs/ROADMAP.md`, especially "Where updates will be pushed from,
   2026-08-27".
4. `docs/plans/2026-08-17-windows-photo-pilot.md`, Sections 5, 9, 10, 11, 19.
   Those are the version identity, launcher, package, manifest and rollback
   machinery this has to work with.
5. `app/install_windows.py`. It already does the hard half.

## What was approved, and by whom

**2026-08-27, Spenser.** Mark presses a button in the app and it updates
itself. Not automatic, not silent, not on a timer. He is told a new version
exists and he chooses. This amends the pilot plan's "no automatic updater,
Spenser installs updates and Mark does not" deliberately rather than by
accident, and the amendment is already in the roadmap.

**2026-08-28, Spenser, in chat.** Five answers, taken as recommended:

1. The app reads `latest.json` from the bucket to learn a version exists. The
   packaging script writes it. The sha256 comes from the zip's own `.sha256`
   sidecar, so Spenser never types a version number or a hash.
2. The notice sits in the masthead beside the version, on every screen.
3. During the download he sees a real bar in megabytes, one sentence per
   stage, and a Cancel that works.
4. At the end the app closes itself and the new version opens on its own.
5. The app checks the bucket once when it starts, in the background, and never
   again that session. A failure to reach it is silent. Settings gets a
   `Check now`.

## Where it comes from

Cloudflare R2 bucket `rrf-app-updates`, public read, verified live and empty on
2026-08-27:

    https://pub-62e06bebd88c4f8cb46a00672f5057b2.r2.dev

Spenser uploads by hand through the Cloudflare dashboard. He uploads three
files, all produced by `tools/package_windows.py`, and hand-writes none of
them:

    Roy R. Fisher v0.5.4.zip
    Roy R. Fisher v0.5.4.zip.sha256
    latest.json

## Measured facts this plan rests on

Measured 2026-08-28 against `build/packages/Roy R. Fisher v0.5.3`:

- The zip is 53.3 MB.
- Unpacked it is 116.8 MB, a ratio of 2.19.
- `install_windows.py` then copies it again into the install home, so a single
  update needs the zip, the unpacked staging tree, and the installed copy on
  disk at the same time: about 287 MB.
- The sidecar is one line, `<hash>  <filename>`, 91 bytes.

## The shape

What happens when Mark clicks Update:

1. The app already knows a newer version exists. It read `latest.json` when it
   started.
2. He clicks. The app says which version and how big, and asks.
3. The app downloads the zip into its own scratch folder in his home area. Not
   into any version folder, not near his jobs.
4. The app checks the zip against the `.sha256` published beside it. Wrong hash
   means delete the download, say so in one sentence, change nothing.
5. The app unzips it into that scratch folder and runs `packaging.verify` on
   the unpacked `program/` folder. That is the same check the launcher already
   runs on every start. Fails means delete it, say so, change nothing.
6. Only now does anything from the package execute. The app starts one separate
   process: the **new** package's `python.exe` running the **new** package's
   `app/update_apply.py`, in its own console window.
7. The app closes itself.
8. That separate process waits until no version of the app is answering any
   more, then calls `install_windows.install()` on the unpacked folder.
9. `install_windows.py` does the rest as it already does: copies into a new
   version folder beside the old one, repoints the Desktop icon, rewrites
   `Start previous version.bat`, prunes to three.
10. The child starts the new version's launcher and exits.

### Why it is shaped that way

**Windows will not let a running program replace its own files.** So the
installer cannot be the app. It has to be a second process that outlives the
first.

**The child runs the new package's Python, not the old one's.** Once the
handoff starts, nothing in the old version folder is held open, so
`install_windows.py` is free to work and `_prune` is free to delete.

**Verify before execute, in that order, twice.** The sha256 catches a broken
download of the whole file. The manifest catches a broken unzip of one file
inside it. Neither runs any code from the package. Step 6 is the first moment
anything from the bucket is executed, and both checks have already passed.

**Rollback is the one that already exists.** `install_windows.py` keeps the
previous version in place and only repoints one Desktop shortcut. A bad update
is undone by running the old version's install file, or by
`Start previous version.bat`. **This slice builds no second rollback mechanism
and changes nothing about that one.**

### What the check honestly does, and does not do

It catches a damaged, truncated, or interrupted download, and a package that
did not unzip completely. That is what it is for and it does it well.

Without code signing it does **not** prove who built the package, and it does
**not** protect against somebody who can rewrite both the zip in the bucket and
the `.sha256` beside it. Anyone able to replace one can replace the other.

That is an integrity check against accident, not a security control against an
adversary. It is the same limit `packaging.py` already states about the
manifest, and it is stated in the same plain words in `updates.py` and on the
screen where Mark decides.

### Every failure ends with a working app

No network, half a download, a bad hash, a bad manifest, a bad zip, no disk
space, the bucket empty or serving nonsense: in every one of them nothing has
been copied, the old version folder is untouched, and the Desktop icon still
points where it pointed. The app says one sentence and carries on.

The two cases where the app is already gone:

- The child starts and then fails. It prints why, keeps its window open, and
  names the Desktop icon. The old version is still installed and the icon still
  points at it.
- The app exits and the child never starts. Mark has a closed app and a working
  Desktop icon.

Both end with the one thing he can always do: double-click his Desktop icon.

### Where the files go

Scratch folder: `~/.rrf-app-download/`. Overridable by `RRF_DOWNLOAD_DIR` for
tests, the same way `RRF_KEY_FILE` and `RRF_INSTALL_HOME` already are.

Deliberately **not** inside the install home. `install_windows.version_folders`
treats every directory there as a version and `_prune` deletes the oldest, so a
scratch folder there would be sorted as a version and eventually deleted as
one. Deliberately not inside a version folder either, where `packaging.verify`
would count it as a file that was not in the package and refuse to start.

The child cannot delete the folder it is running from, so the scratch folder is
cleared at the start of every update attempt rather than at the end of one.
One rule, and it is stated in the module.

## Global constraints

- Python 3.9 compatible. No `int | None`, no `match`.
- Standard library only in `updates.py` and `app/update_apply.py`. Neither may
  import a third-party package. `update_apply.py` runs before anything has
  proved the new package's wheels are usable, and `updates.py` sits beside
  `packaging.py` and `startup.py`, which are stdlib-only for the same reason.
- No em dashes anywhere: code, comments, docs, UI copy.
- Never move, print, or log a key. Nothing in this slice reads one.
- Nothing touches a folder of Mark's.
- Commits on this branch are recovery checkpoints. Nothing is pushed, merged,
  packaged, or delivered without Spenser's explicit yes.
- The full suite ends green after every task: 1,052 Python and 60 Vitest as of
  the branch point. Ask the suite for the real numbers rather than trusting
  this line.

## What this slice does not do

- It does not cut a package and it does not change `VERSION`. Packaging 0.5.4
  and putting anything in the bucket are separate decisions for Spenser.
- It does not build a second rollback.
- It does not put `Start previous version.bat` anywhere easier to find. That is
  a real gap, it is named in the roadmap fold-back, and it is a different job.
- It does not run on the Mac. `packaging.is_checkout` is true in a development
  checkout, and in a checkout the update check does not run and the button does
  not render. The modules are tested on the Mac against a local fake bucket and
  a fake package; the spawn is proved on the Mac with a harmless child.

## The tasks

### Task 1: One place that knows 0.10.0 is newer than 0.9.0

- [ ] Move `install_windows._as_numbers` into `packaging.py` as a named,
      documented function, and add `newer(a, b)`. Both stdlib only.
- [ ] `install_windows.py` uses it instead of its own copy. Behaviour of
      `version_folders` is unchanged, which its existing tests already assert.
- [ ] Test: `0.10.0` sorts above `0.9.0`, a non-numeric part never raises, an
      empty string is never newer than anything, and equal versions are not
      newer than each other.
- [ ] Suite green.

### Task 2: Reading the bucket

- [ ] New `app/server/updates.py`. Its docstring states the shape above, the
      scratch-folder reasoning, and the honest limit of the check. Stdlib only.
- [ ] `BUCKET` constant holds the R2 base URL, in one place, with a comment
      saying it is public on purpose because Mark's machine downloads with no
      login and the package holds no key and no client material.
- [ ] `check()` fetches `latest.json`, bounded timeout, bounded response size.
      Returns what is known or an empty answer. It never raises to a caller.
- [ ] `latest.json` shape: `version`, `zip`, `size`. Nothing else is read. A
      missing field, a wrong type, unparseable JSON, a 404, a timeout, and a
      body that is not JSON all mean the same thing: nothing is known, nothing
      is shown, nothing changes.
- [ ] The `zip` field is a filename and is refused if it contains a slash, a
      backslash, a colon, or `..`. It is joined to the bucket URL and must
      never be able to point somewhere else.
- [ ] An announced version that is not newer than the running version is not an
      update and shows nothing.
- [ ] In a checkout (`packaging.is_checkout`) `check()` does nothing and
      reports nothing.
- [ ] Tests against a local HTTP server standing in for the bucket, in
      `test_update_check.py`: newer, same, older, missing file, 404, timeout,
      HTML instead of JSON, JSON with no version, a `zip` field trying to
      escape, an oversized body, and the checkout gate. Every one of them
      leaves the app reporting no update and changes nothing on disk.
- [ ] Suite green.

### Task 3: The download, and the hash

- [ ] `updates.download()` writes into the scratch folder, clearing it first.
- [ ] Before a byte is fetched, check free space with `shutil.disk_usage`
      against a floor derived from the announced size. Measured 2026-08-28: an
      update needs the zip plus 2.19 times the zip unpacked plus the same again
      installed. The floor is stated as that arithmetic in the code, with the
      measurement in the comment, not as a magic number. Too little space is a
      plain refusal before any network call.
- [ ] Progress is reported through a module in the shape of `progress.py`: a
      dictionary behind a lock, worthless a second after the run ends, never
      written to disk.
- [ ] Cancel is a `threading.Event` checked between chunks. Cancelling deletes
      the partial file and the scratch folder and reports plainly.
- [ ] `updates.verify_download()` fetches `<zip>.sha256`, parses the first
      whitespace-separated token as the hash, and compares it with the sha256
      of the file on disk. A mismatch deletes the download and refuses.
- [ ] An unreadable, empty, or malformed sidecar is a refusal, never a skip.
      A download whose hash cannot be checked is never treated as good.
- [ ] Tests in `test_update_download.py`: a good download verifies; a truncated
      file is refused and deleted; a byte flipped is refused; a missing sidecar
      is refused; a sidecar with no hash in it is refused; too little free space
      refuses before the network is touched; cancel mid-download leaves nothing
      behind. Each asserts that no process was spawned and nothing outside the
      scratch folder changed.
- [ ] Suite green.

### Task 4: Unpacking, and the manifest

- [ ] `updates.unpack()` extracts into the scratch folder.
- [ ] Every entry name is checked before extraction: no absolute path, no `..`,
      no backslash, no colon, and every entry inside one top-level folder. This
      mirrors `package_windows._arcname` in reverse. Python's own extractor
      sanitizes silently; this refuses loudly and names the entry.
- [ ] The sum of the declared uncompressed sizes is checked against a ceiling
      before extracting, so a small file cannot ask for an enormous unpack.
- [ ] After extraction, `packaging.verify(packaging.program_dir(unpacked))`.
      A failure deletes the unpacked tree and refuses with the sentence
      `packaging.py` already wrote.
- [ ] `packaging.version_of` on the unpacked tree must equal the version
      `latest.json` announced. A package that says it is a different version
      than the one advertised is refused.
- [ ] Tests in `test_update_unpack.py`: a good package unpacks and verifies; an
      entry escaping the top folder is refused and named; a zip declaring an
      absurd uncompressed size is refused; a package whose manifest does not
      match is refused with the manifest's own wording; a package whose VERSION
      disagrees with `latest.json` is refused. Each asserts nothing was spawned.
- [ ] Suite green.

### Task 5: The child that does the installing

- [ ] New `app/update_apply.py`, beside `run_app.py` and `install_windows.py`.
      Stdlib only. Its docstring says why it exists in one paragraph: Windows
      will not let a running program replace its own files.
- [ ] Arguments: the unpacked package folder, and nothing else it could get
      wrong. It finds the install home the same way `install_windows.py` does.
- [ ] It waits for the coast to clear by calling
      `install_windows._refuse_if_anything_is_running` on a bounded loop,
      because that is the exact condition the install needs rather than a proxy
      for it. Bounded at 90 seconds.
- [ ] Still running after the bound: it refuses plainly, names the version that
      is still up, says nothing was changed, and keeps its window open.
- [ ] Coast clear: it calls `install_windows.install(unpacked)` and prints what
      that already prints.
- [ ] On success it starts the newly installed version's launcher and exits.
- [ ] On any failure it prints the reason, states that the previous version is
      still installed and still works, names the Desktop icon, and keeps the
      window open.
- [ ] It never deletes the folder it is running from.
- [ ] Tests in `test_update_apply.py`, with `RRF_INSTALL_HOME` and
      `RRF_DESKTOP` pointed at temporary folders: it waits while something is
      answering; it refuses after the bound and names the version; it installs
      when nothing is answering; a failed install leaves the previous version
      folder present and the message names the Desktop icon.
- [ ] Suite green.

### Task 6: The handoff, and the app closing itself

- [ ] `updates.hand_off()` builds the command line: the unpacked package's
      `program/python/python.exe` and its `program/app/update_apply.py`. Never
      the running version's copies of either.
- [ ] It refuses to spawn unless both the hash check and the manifest check
      have passed in this run. The state that records that lives in the module
      and is not something a caller can assert on its own behalf.
- [ ] On Windows it spawns with `CREATE_NEW_CONSOLE` so the child has its own
      visible window, which is where its plain messages land. The pilot's
      "keep the console visible" decision applies to the child as much as to
      the launcher.
- [ ] If the spawn raises, the app does **not** exit. It reports plainly and
      stays up.
- [ ] `updates.close_the_app()` clears `runtime.json` through
      `startup.clear_runtime` and then exits the process. It takes the exit
      function as an argument so a test can watch it without dying. It is
      called from a short timer thread so the HTTP answer reaches the browser
      first.
- [ ] Tests in `test_update_handoff.py`: the command line names the new
      package's python and the new package's `update_apply.py`; nothing is
      spawned when either check has not passed; a spawn that raises leaves the
      app alive and never calls exit; the close helper clears `runtime.json`
      before exiting; a real harmless child spawned on the Mac outlives its
      parent, which is the one thing about detachment worth proving rather than
      asserting.
- [ ] Suite green.

### Task 7: The endpoints

- [ ] `GET /api/update` reports the running version, the available version if
      one is known, its size, and the state of any run in progress.
- [ ] `POST /api/update/check` looks now. This is the `Check now` on Settings.
- [ ] `POST /api/update/start` runs download, verify, unpack, hand off, close.
- [ ] `GET /api/update/progress` is what the screen polls.
- [ ] `POST /api/update/cancel` stops it.
- [ ] The startup check runs once, in a background thread, off the startup
      path, in the shape of the existing `tidy_cache` thread in `run_app.py`.
      It never delays serving and it never says anything when it fails.
- [ ] `busy.writing()` is held where it should be, so an update cannot start
      while a demo reset holds the floor and the reverse.
- [ ] Two updates cannot run at once.
- [ ] Tests in `test_update_api.py`: each route's shape; start refuses when one
      is already running; cancel during a run; the routes report no update in a
      checkout; a failed run leaves the app answering normally afterwards.
- [ ] Suite green.

### Task 8: What Mark sees

- [ ] The masthead's `v0.5.3` becomes a quiet button when an update is known,
      reading `Update available`. It renders on every screen because the
      masthead does. With no update known it is exactly what it is today.
- [ ] Clicking it opens the step, in the app's existing `confirm` shape: which
      version, how big in megabytes, what will happen in three short sentences,
      and the honest limit of the check in one. Then `Update now` and
      `Not now`. The choice lives inside the action, which is the rule.
- [ ] During the run: a real bar in megabytes of the total, and one sentence
      per stage. `Downloading 12 MB of 53 MB`, then `Checking the download`,
      then `Unpacking`, then `Installing`. A `Cancel` that works during the
      download.
- [ ] The last screen before the app goes: `Closing now. The new version will
      open in a few seconds. If it does not, use the Roy R. Fisher icon on your
      Desktop.`
- [ ] Every failure renders as one plain sentence in the app's existing `error`
      shape, and the app is still usable underneath it.
- [ ] `Check now` on Settings, with a plain answer either way, including
      `You are on the newest version` and a sentence when the bucket could not
      be reached. The startup check is silent; this one is not, because he
      asked.
- [ ] Vitest: the button appears only when an update is known; the step shows
      the version and the size; progress renders megabytes; cancel calls the
      route; the closing screen appears; a failed run leaves the app usable.
- [ ] Suite green.

### Task 9: Packaging

- [ ] `tools/package_windows.py` copies `app/update_apply.py` into the package
      the same way it already copies `run_app.py` and `install_windows.py`.
- [ ] It writes `latest.json` beside the zip and the sidecar, holding the
      version, the zip's filename, and its size in bytes. Machine-written, so
      Spenser uploads three files and types none of their contents.
- [ ] `latest.json` is a sibling of the zip and is never inside the package,
      the same way the zip and the sidecar already are.
- [ ] Add to `test_package_manifest.py`: `app/update_apply.py` is present in
      the built package. Without it, an update installs a version that cannot
      itself be updated.
- [ ] Add to `test_package_zip.py`: `latest.json` is written, its fields match
      the built zip, and it is not inside the archive.
- [ ] Note in the packaging script's own output what the three files to upload
      are, so the dashboard step is not remembered from a chat message.
- [ ] Suite green.

### Task 10: The honesty pass

- [ ] Read every new sentence that reaches Mark's screen and every refusal
      message against `HOW-WE-WORK.md`: main point first, short sentences,
      common words, no term he would not recognise, no em dashes.
- [ ] No message states a fact the app has not observed. In particular nothing
      claims the update is safe, verified, or signed. It says the download
      matched its checksum, which is what happened.
- [ ] One line in `README FIRST.txt` about the button, written by
      `package_windows.readme_text`, so the packaged readme and the app do not
      drift.
- [ ] Confirm no new file, log, or error can carry key material. Nothing in
      this slice reads a key; this is the check that it stayed that way.
- [ ] Suite green.

### Task 11: The stop

- [ ] Full suite green, Python and Vitest, with the real counts reported to
      Spenser rather than the counts written at the top of this plan.
- [ ] A screen stop: Spenser clicks through the masthead button, the step, a
      cancelled run, and a failed run, against the "a click leads to a step"
      rule. This is a screen change, so the stop is required.
- [ ] Report what is proven on the Mac and what still needs Windows. Name it
      plainly: nothing in this slice has installed anything on Windows, and the
      first real proof is Spenser running it end to end on the Windows machine
      before Mark ever sees it. Gate D still stands.
- [ ] Spenser's explicit yes before anything is packaged, uploaded, pushed, or
      merged.

### Task 12: The plan destroys itself

- [ ] Fold into `docs/ROADMAP.md`: the five decisions of 2026-08-28, the shape
      of the handoff and why it is that shape, the measured sizes, the scratch
      folder reasoning, the honest limit of the check, what is proven on the
      Mac and what is not, and the fact that `Start previous version.bat` sits
      somewhere Mark will not find.
- [ ] Add to the roadmap's "Still owed" list: putting the rollback somewhere he
      can reach.
- [ ] `git rm docs/plans/2026-08-28-in-app-update.md`.
- [ ] Suite green, including `test_plans_delete_themselves.py`.
