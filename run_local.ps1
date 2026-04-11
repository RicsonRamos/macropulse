# MacroPulse Local Runner - FINAL VERSION
Write-Host "Iniciando MacroPulse Intelligence - modo local" -ForegroundColor Cyan

# Ports
$backendPort = 8000
$frontendPort = 8050

# Kill processes on ports
function Stop-Port {
    param ($port)
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn) {
        foreach ($c in $conn) {
            try {
                Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
                Write-Host "Porta $port liberada" -ForegroundColor Yellow
            } catch { }
        }
    }
}

Stop-Port $backendPort
Stop-Port $frontendPort

# Caminho do venv
$venvPath = "$PSScriptRoot\.venv\Scripts\Activate.ps1"
if (-Not (Test-Path $venvPath)) {
    Write-Host "ERRO: Ambiente virtual (.venv) não encontrado." -ForegroundColor Red
    exit
}

# Start Backend
Write-Host "Iniciando backend (FastAPI)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot'; . '$venvPath'; uvicorn backend.api.main:app --reload --host 127.0.0.1 --port $backendPort"

# Start Frontend
Write-Host "Iniciando frontend (Servidor Web)..." -ForegroundColor Magenta
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\frontend'; . '$venvPath'; python -m http.server $frontendPort"

# Final
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   ESTAÇÃO MACROPULSE PRONTA PARA USO     " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Dashboard: http://localhost:8050"
Write-Host "API Docs:  http://localhost:8000/docs"
Write-Host ""
Write-Host "Use Ctrl+C para encerrar este controlador."