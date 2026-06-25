@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -3 dashboard.py
    goto :done
)

where python >nul 2>nul
if %ERRORLEVEL%==0 (
    python dashboard.py
    goto :done
)

echo Python was not found. Please install Python 3 and make sure it is available in PATH.
echo You can also run this manually from the project root:
echo python otb-legacy-source\dashboard.py

:done
pause
