# Automated Setup Script for AI Car Mechanic Chatbot
Write-Host "== Starting AI Car Mechanic Chatbot Full Installation ==" -ForegroundColor Green

# 1. Python Virtual Environment Setup
If (-Not (Test-Path ".venv")) {
    Write-Host "[1/4] Creating Python Virtual Environment (.venv)..." -ForegroundColor Yellow
    python -m venv .venv
} Else {
    Write-Host "[1/4] Virtual Environment (.venv) already exists." -ForegroundColor Cyan
}

# 2. Install Python Dependencies
Write-Host "[2/4] Installing Python packages in .venv..." -ForegroundColor Yellow
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. Run Django Migrations
Write-Host "[3/4] Running Django Database Migrations..." -ForegroundColor Yellow
.\.venv\Scripts\python.exe manage.py migrate

# 4. Install Frontend NPM Packages
Write-Host "[4/4] Installing Frontend Node modules..." -ForegroundColor Yellow
Set-Location frontend
npm install
Set-Location ..

Write-Host "== Setup Completed Successfully! ==" -ForegroundColor Green
Write-Host "----------------------------------------------------" -ForegroundColor Gray
Write-Host "To start the application:" -ForegroundColor White
Write-Host "1. Backend:  .\.venv\Scripts\python.exe manage.py runserver 8000" -ForegroundColor Cyan
Write-Host "2. Frontend: cd frontend; npm run dev" -ForegroundColor Cyan
Write-Host "----------------------------------------------------" -ForegroundColor Gray
