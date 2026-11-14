Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Starting ASTROHEALTH Mission Control System   " -ForegroundColor White
Write-Host "   Intelligent Health Monitoring Beyond Earth     " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Check if MongoDB is running
$socket = New-Object Net.Sockets.TcpClient
$connected = $false
try {
    $socket.Connect("127.0.0.1", 27017)
    $connected = $true
    $socket.Close()
} catch {}

if (-not $connected) {
    Write-Host "[!] Warning: MongoDB does not appear to be running on port 27017." -ForegroundColor Yellow
    Write-Host "    Please ensure MongoDB is started." -ForegroundColor Yellow
} else {
    Write-Host "[+] MongoDB connected on localhost:27017" -ForegroundColor Green
}

# 1. Start Backend in a new PowerShell window
Write-Host "[+] Launching AstroHealth Backend & AI Simulator Engine on port 8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; Write-Host '--- ASTROHEALTH BACKEND & AI SIMULATOR ---' -ForegroundColor Cyan; & 'd:\spaceZ\.venv\Scripts\python.exe' -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

# 2. Start Frontend in a new PowerShell window
Write-Host "[+] Launching AstroHealth Frontend on port 5173..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; Write-Host '--- ASTROHEALTH FRONTEND UI ---' -ForegroundColor Cyan; npm run dev"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host " AstroHealth services launched successfully!      " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "Web Console:   http://localhost:5173" -ForegroundColor White
Write-Host "Swagger Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "WebSocket:     ws://localhost:8000/ws/telemetry" -ForegroundColor White
Write-Host ""
Write-Host "Default Login Accounts:" -ForegroundColor Yellow
Write-Host "  - Astronaut:       astro_alex / AstroPassword123!" -ForegroundColor White
Write-Host "  - Medical Officer: dr_vance   / DoctorPassword123!" -ForegroundColor White
Write-Host "  - Administrator:   admin      / AdminPassword123!" -ForegroundColor White
Write-Host ""

