# EXFIN WhatsApp Server Diagnostic Script
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
# Run this on your remote server to find out why 8080 is not working.

Write-Host "--- SYSTEM CHECK ---" -ForegroundColor Cyan
$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) { Write-Host "✅ Node.js: $($node.Source)" -ForegroundColor Green } else { Write-Host "❌ Node.js NOT FOUND" -ForegroundColor Red }

$pm2 = Get-Command pm2 -ErrorAction SilentlyContinue
if ($pm2) { Write-Host "✅ PM2: $($pm2.Source)" -ForegroundColor Green } else { Write-Host "❌ PM2 NOT FOUND. Use 'npm install -g pm2'" -ForegroundColor Red }

Write-Host "`n--- PORT CHECK (8080) ---" -ForegroundColor Cyan
$port8080 = netstat -ano | findstr :8080
if ($port8080) { 
    Write-Host "✅ Port 8080 is LISTENING" -ForegroundColor Green
    Write-Host $port8080
}
else { 
    Write-Host "❌ Port 8080 is NOT LISTENING" -ForegroundColor Red 
}

Write-Host "`n--- DB CONNECTIVITY ---" -ForegroundColor Cyan
# Attempt a simple socket test to localhost:5432
$tcp = New-Object System.Net.Sockets.TcpClient
try {
    $tcp.Connect("localhost", 5432)
    Write-Host "✅ PostgreSQL (5432) is reachable" -ForegroundColor Green
    $tcp.Close()
}
catch {
    Write-Host "❌ PostgreSQL (5432) is NOT reachable or blocked" -ForegroundColor Red
}

Write-Host "`n--- PM2 STATUS ---" -ForegroundColor Cyan
if ($pm2) {
    & pm2 status exfin-whatsapp-api
    Write-Host "`nCheck logs with: 'pm2 logs exfin-whatsapp-api'" -ForegroundColor Yellow
}

Write-Host "`n--- REPAIR COMMAND ---" -ForegroundColor Cyan
Write-Host "If things are broken, try running the installer again on the server:" -ForegroundColor White
Write-Host "powershell -ExecutionPolicy Bypass -File infrastructure\whatsapp\install.ps1" -ForegroundColor Yellow
