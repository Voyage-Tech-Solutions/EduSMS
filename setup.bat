@echo off
echo ========================================
echo EduSMS Project Setup
echo ========================================
echo.

echo [1/4] Setting up Backend...
cd backend

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing backend dependencies...
pip install -r requirements.txt

if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo Please edit backend\.env with your Supabase credentials
)

cd ..

echo.
echo [2/4] Setting up Frontend...
cd frontend

if not exist node_modules (
    echo Installing frontend dependencies...
    call npm install
)

if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo Please edit frontend\.env with your configuration
)

cd ..

echo.
echo [3/4] Creating logs directory...
if not exist backend\logs mkdir backend\logs

echo.
echo [4/4] Setup complete!
echo.
echo ========================================
echo Next Steps:
echo ========================================
echo 1. Edit backend\.env with your Supabase credentials
echo 2. Edit frontend\.env with your API URL
echo 3. Run database schema: backend\database\schema.sql in Supabase
echo 4. Start backend: cd backend ^&^& venv\Scripts\activate ^&^& uvicorn app.main:app --reload
echo 5. Start frontend: cd frontend ^&^& npm run dev
echo.
echo For more details, see README.md
echo ========================================
pause
