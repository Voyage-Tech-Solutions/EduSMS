@echo off
echo Checking Frontend Environment Variables...
echo.
cd frontend
echo NEXT_PUBLIC_API_URL should be: https://edusms-ke1l.onrender.com
echo.
echo Current .env file:
type .env
echo.
echo.
echo To apply changes:
echo 1. Stop your dev server (Ctrl+C)
echo 2. Run: npm run dev
echo 3. Or commit and push to trigger Vercel redeploy
echo.
pause
