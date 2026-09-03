@echo off
REM Double-click this file to start the Roy R. Fisher app.
REM
REM It starts the app with no window of its own and closes immediately. The app
REM opens in your browser a moment later.
REM
REM `pythonw.exe` is the same Python beside it, built to run without a console.
REM Nothing is printed anywhere, on purpose: a black window sitting in front of
REM the app was the first thing anybody saw, every time. Anything that goes
REM wrong now arrives as a message box instead, and is written to the log in
REM your user folder.
REM
REM `start ""` hands the app to Windows and lets this file finish, so the
REM console this .bat runs in closes at once rather than waiting.

cd /d "%~dp0"
start "" "program\python\pythonw.exe" "program\app\run_app.py"
