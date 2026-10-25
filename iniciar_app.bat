@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo No se encontro el entorno virtual .venv.
    echo Abra PowerShell en esta carpeta y ejecute: python -m venv .venv
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m streamlit run app.py
pause
