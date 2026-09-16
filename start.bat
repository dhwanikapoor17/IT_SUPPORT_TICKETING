@echo off
echo ===================================================
echo Starting IT Support Ticketing System
echo ===================================================

echo [1/2] Launching Backend API (FastAPI)...
start "IT Support Ticketing - Backend (Port 8000)" cmd /k "cd /d %~dp0backend && .\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Launching Frontend (Next.js)...
start "IT Support Ticketing - Frontend (Port 3000)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Waiting for servers to initialize...
timeout /t 3 /nobreak >nul

echo Opening browser at http://localhost:3000...
start http://localhost:3000

echo.
echo Both servers have been launched in separate terminal windows!
echo Backend API Docs: http://127.0.0.1:8000/docs
echo Frontend Web App: http://localhost:3000
echo ===================================================
pause
