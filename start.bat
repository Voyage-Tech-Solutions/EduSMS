@echo off
echo Starting EduSMS Platform...
echo.

start "EduSMS Backend" cmd /k "cd backend && venv\Scripts\activate && uvicorn app.main:app --reload"
timeout /t 3 /nobreak > nul

start "EduSMS Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo EduSMS is starting...
echo ========================================
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo ========================================
