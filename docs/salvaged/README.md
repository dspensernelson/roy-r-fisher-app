# Salvaged

Files rescued from the stale `RRF/app` copy before it was deleted on 2026-08-21.

Nothing here is wired into the running app. This folder exists so that code
which existed in only one place could not be lost during the cleanup.

## scan.py

The only source file that existed in `RRF/app/server` but never in this
repository. It turned the engine's readiness result into the rows the job
screen drew, and imported `app/engine/readiness_scan.py`.

It appears superseded by `app/server/browse.py` and `app/server/inventory.py`,
but that was never proven, so it was kept rather than dropped.

Original location: `RRF/app/server/scan.py` (57 lines).
Also recoverable from the RRF repository's own history.
