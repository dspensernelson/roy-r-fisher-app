@echo off
REM Double-click this file to start the Roy R. Fisher app.
REM
REM It checks the folder unzipped completely, starts the app, and opens your
REM browser. Leave the window open while you work.
REM
REM If something is wrong it prints the reason here and pauses, so the window
REM stays open long enough to read it.

cd /d "%~dp0"

program\python\python.exe program\app\run_app.py
if errorlevel 1 (
  echo.
  echo The app did not start. The reason is above this line.
  pause
)
