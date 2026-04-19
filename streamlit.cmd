@echo off
setlocal

set "VENV_STREAMLIT=%~dp0.venv\Scripts\streamlit.exe"
if exist "%VENV_STREAMLIT%" (
    "%VENV_STREAMLIT%" %*
    exit /b %ERRORLEVEL%
)

set "UV_CACHE_DIR=C:\codex\.uv-cache"
uv run --with-requirements "%~dp0requirements.txt" streamlit %*
exit /b %ERRORLEVEL%
