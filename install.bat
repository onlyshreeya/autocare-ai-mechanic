@echo off
echo ===================================================
echo 🚗 Starting AI Car Mechanic Chatbot Full Setup...
echo ===================================================

if not exist .venv (
    echo Creating Python virtual environment...
    python -m venv .venv
)

echo Installing Python dependencies into .venv...
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

echo Running database migrations...
.\.venv\Scripts\python.exe manage.py migrate

echo Installing Frontend dependencies...
cd frontend
call npm install
cd ..

echo ===================================================
echo 🎉 Setup complete!
echo To run backend:  .\.venv\Scripts\python.exe manage.py runserver 8000
echo To run frontend: cd frontend ^&^& npm run dev
echo ===================================================
pause
