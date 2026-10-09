@echo off
setlocal

cd /d "%~dp0"

if not exist "server\.venv\Scripts\python.exe" (
  echo Backend virtual environment is missing.
  echo Run setup again before starting the app.
  pause
  exit /b 1
)

if not exist "apps\web\dist\index.html" (
  echo Web app build is missing.
  echo Run npm run build from apps\web before starting the app.
  pause
  exit /b 1
)

echo Starting Brainrot Study at http://localhost:8000
echo Keep this window open while you use the app. Press Ctrl+C to stop it.
echo.

cd server
start "" "http://localhost:8000"
".venv\Scripts\python.exe" -m app

pause
