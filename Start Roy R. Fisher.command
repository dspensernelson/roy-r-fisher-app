#!/bin/bash
# Double-click this file to start the Roy R. Fisher app.
#
# A thin shim on purpose. Everything it used to do itself, checking whether the
# app was already running and on which port, now lives in app/run_app.py so the
# Mac and Windows take the same path and the logic exists in one place instead
# of once in bash and once in batch.

cd "$(dirname "$0")" || exit 1

python3 app/run_app.py
status=$?
if [ $status -ne 0 ]; then
  echo
  echo "The app did not start. The reason is above this line."
  read -r -p "Press Return to close this window. "
fi
exit $status
