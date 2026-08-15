#!/bin/bash
# Double-click this file to start the Roy R. Fisher app.
#
# It starts the app and opens your browser. If the app is already running it
# just opens the browser instead of trying to start a second copy.
#
# The folder your jobs live in is set inside the app now, on a screen, and
# the app remembers it. Nothing about it is in this file any more.

cd "$(dirname "$0")" || exit 1

if curl -s -o /dev/null --max-time 2 http://127.0.0.1:8000; then
  echo "The app is already running. Opening it."
  open http://127.0.0.1:8000
  exit 0
fi

echo "Starting the Roy R. Fisher app."
echo "Whether captions can be written is decided inside the app, and the"
echo "Photos screen says which it is."
echo
echo "Your browser will open in a second."
echo "Leave this window open while you work. To stop the app, press Control and C."
echo

python3 app/run_app.py
