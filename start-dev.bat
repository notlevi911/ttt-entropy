@echo off
echo 🎮 Starting Entropy TicTacToe Development Environment
echo ==================================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH  
    pause
    exit /b 1
)

echo ✅ Python and Node.js are available

REM Start backend server
echo 🚀 Starting FastAPI backend server...
cd backend
start "Entropy TicTacToe Backend" cmd /c "python main.py"
cd ..

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend server  
echo 🎨 Starting React frontend server...
cd frontend
start "Entropy TicTacToe Frontend" cmd /c "npm start"
cd ..

echo.
echo 🎉 Development environment started successfully!
echo.
echo 📍 Access points:
echo    Frontend: http://localhost:3000
echo    Backend:  http://localhost:8000
echo.
echo 🎮 How to play:
echo    1. Open http://localhost:3000 in two browser windows/tabs
echo    2. Create a room in one window
echo    3. Join the room from the second window  
echo    4. Enjoy playing Entropy TicTacToe!
echo.
echo 🛑 To stop servers: Close the terminal windows that opened
echo.
pause