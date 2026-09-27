@echo off
cd /d "%~dp0"
where py >nul 2>nul && (set PY=py -3) || (set PY=python)
if not exist .venv (
  echo First run: installing... ^(needs Python 3.10+ from python.org^)
  %PY% -m venv .venv || (echo Install Python from https://www.python.org/downloads/ and tick "Add to PATH" & pause & exit /b 1)
  .venv\Scripts\python -m pip install --upgrade pip >nul
  .venv\Scripts\python -m pip install -r requirements.txt || (pause & exit /b 1)
)
.venv\Scripts\python -m photoprint %*
pause
