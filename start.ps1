# Start IT Support Ticketing System (PowerShell)
$root = $PSScriptRoot

Write-Host "Starting Backend API (FastAPI) on port 8000..." -ForegroundColor Cyan
Start-Process cmd -ArgumentList "/k cd /d `"$root\backend`" && .\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

Write-Host "Starting Frontend (Next.js) on port 3000..." -ForegroundColor Cyan
Start-Process cmd -ArgumentList "/k cd /d `"$root\frontend`" && npm run dev"

Start-Sleep -Seconds 3
Start-Process "http://localhost:3000"

Write-Host "`nServers launched!" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000"
Write-Host "Backend API docs: http://127.0.0.1:8000/docs"
