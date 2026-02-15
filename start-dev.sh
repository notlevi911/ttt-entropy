#!/bin/bash

# Start Entropy TicTacToe Development Servers

echo "🎮 Starting Entropy TicTacToe Development Environment"
echo "=================================================="

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ Port $port is already in use"
        return 1
    fi
    return 0
}

# Check if required ports are available
if ! check_port 8000; then
    echo "Backend port 8000 is busy. Please stop the process using it."
    exit 1
fi

if ! check_port 3000; then
    echo "Frontend port 3000 is busy. Please stop the process using it."
    exit 1
fi

echo "✅ Ports 8000 and 3000 are available"

# Start backend in background
echo "🚀 Starting FastAPI backend server..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if ! curl -s http://localhost:8000 >/dev/null; then
    echo "❌ Failed to start backend server"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ Backend server running at http://localhost:8000"

# Start frontend
echo "🎨 Starting React frontend server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "🎉 Development environment started successfully!"
echo ""
echo "📍 Access points:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo ""
echo "🎮 How to play:"
echo "   1. Open http://localhost:3000 in two browser windows/tabs"
echo "   2. Create a room in one window"
echo "   3. Join the room from the second window"
echo "   4. Enjoy playing Entropy TicTacToe!"
echo ""
echo "🛑 To stop servers: Press Ctrl+C or run 'kill $BACKEND_PID $FRONTEND_PID'"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Cleanup complete!"
    exit 0
}

# Set trap for cleanup on script exit
trap cleanup SIGINT SIGTERM

# Keep script running
echo "💡 Press Ctrl+C to stop all servers"
wait