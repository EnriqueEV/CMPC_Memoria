@echo off
echo ============================================
echo   CMPC - Gestor de Accesos SAP
echo   Abriendo en http://localhost:8501
echo ============================================
cd /d "%~dp0"

REM Intenta usar conda si existe, si no usa streamlit directamente
where conda >nul 2>&1
if %ERRORLEVEL% equ 0 (
    conda run -p .conda --no-capture-output streamlit run app/app.py --server.port 8501 --server.headless false
) else (
    C:\Users\under\anaconda3\Scripts\conda.exe run -p .conda --no-capture-output streamlit run app/app.py --server.port 8501 --server.headless false
)
pause
