@echo off
cd /d "%~dp0"
echo Starting FutureSkill AI...
where py >nul 2>&1
if %errorlevel%==0 (
  py app.py
) else (
  python app.py
)
pause
