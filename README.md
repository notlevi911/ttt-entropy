# Entropy TicTacToe

A multiplayer strategy game that combines traditional TicTacToe with hidden information and probability mechanics.

## How It Works

The game uses a 3x3 board with 9 hidden pieces. Each board contains exactly 5 pieces of one symbol (X or O) and 4 of the other, but players don't know which symbol has the majority. Every piece shows probability percentages that update as the game progresses.

**Placement Phase**: Players alternate placing pieces on empty cells. All symbols remain hidden.

**Reveal Phase**: Players take turns revealing pieces to find their symbols and form three in a row.

The key challenge is using probability information and deduction to make strategic decisions about where to place and reveal pieces.

[Setup Instructions](#setup)

## Game Rules

- 3x3 grid with 9 total pieces
- Exactly 5 of one symbol, 4 of the other
- Players don't know which symbol they need
- Each piece displays probability percentages (randomly assigned which number represents X or O)
- Probabilities update after each reveal following Monty Hall theorem to determine the new percentages
- Win by getting 3 symbols in a row, column, or diagonal
- Two phases: placement then reveal

## Technical Details

- Frontend: React with TypeScript
- Backend: FastAPI with WebSocket communication
- Real-time multiplayer with room-based matchmaking
- Server-authoritative game logic

## Setup

### Requirements

- Python 3.8 or higher
- Node.js 16 or higher
- npm package manager

### Backend Setup

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate    # Windows
   source venv/bin/activate # macOS/Linux
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run server:
   ```bash
   python main.py
   ```
   Server runs on http://localhost:8000

### Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start development server:
   ```bash
   npm start
   ```
   Frontend runs on http://localhost:3000

### Playing the Game

1. Open http://localhost:3000 in two browser windows
2. One player creates a room and shares the room code
3. Second player joins using the room code
4. Game starts automatically when both players are ready

### Development

The backend uses in-memory storage, so rooms reset when the server restarts. For production use, consider adding persistent storage.

WebSocket endpoints:
- `GET /create_room` - Create new room
- `WebSocket /ws/{room_code}` - Game communication

Game state is managed server-side to prevent cheating.