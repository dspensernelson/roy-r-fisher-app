@echo off
REM Double-click this file to install the Roy R. Fisher app, or to update it
REM to this version. It is the same action either way.
REM
REM It copies the app into your own account, puts one icon on your Desktop,
REM and leaves the version you had in place in case you need to go back to it.
REM Nothing of yours is touched: your key, your jobs folder, your settings and
REM your documents all live outside the app and are not moved or changed.
REM
REM A thin shim on purpose. Everything it does lives in app\install_windows.py,
REM so there is one place for it to be right and one place to test.

cd /d "%~dp0"

python\python.exe app\install_windows.py
echo.
pause
