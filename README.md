# 🎮 Entropy TicTacToe

A multiplayer hidden-information strategy game that reimagines classic TicTacToe using constrained probability, deduction, and psychological gameplay.

## 🧠 Game Concept

Entropy TicTacToe is a probabilistic deduction-based multiplayer board game where:

- The board contains 9 hidden pieces
- Exactly 5 of one symbol and 4 of the other exist  
- At game start, the majority symbol (5X/4O or 5O/4X) is randomly chosen
- The majority is hidden from players
- Each piece displays two probabilities (e.g., 82% / 18%)
- Players do not know which probability corresponds to their symbol
- Probabilities dynamically update as the game progresses

## 🏗️ Tech Stack

- **Frontend**: React with TypeScript
- **Backend**: FastAPI (Python)
- **Real-time Communication**: WebSockets
- **State Management**: In-memory server state

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   source venv/bin/activate  # On macOS/Linux
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the FastAPI server:
   ```bash
   python main.py
   ```

   The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the React development server:
   ```bash
   npm start
   ```

   The frontend will be available at `http://localhost:3000`

## 🎯 How to Play

### Phase 1 - Placement Phase
1. Join a room using a 6-character room code
2. Two players take turns placing probability pieces on empty cells
3. All pieces remain hidden during placement
4. The center piece probability stays hidden until placement ends
5. After all 9 pieces are placed → transition to Reveal Phase

### Phase 2 - Reveal Phase  
1. Players take turns revealing any hidden cell
2. Each reveal shows the actual symbol (X or O)
3. Probabilities update dynamically after each reveal
4. First player to get 3 in a row wins
5. If all pieces are revealed with no winner → draw

## 🔢 Game Rules

- **Board Structure**: 3×3 grid (9 total cells)
- **Symbol Distribution**: Exactly 5 of one symbol, 4 of the other
- **Hidden Information**: Majority symbol is unknown to both players
- **Probability Display**: Each piece shows percentages like "82% / 18%"
- **Dynamic Updates**: Probabilities change based on revealed information
- **Win Condition**: 3 symbols in a row, column, or diagonal
- **No Extra Turns**: Players alternate after each action

## 🎨 Features

- **Real-time Multiplayer**: WebSocket-based gameplay
- **Live Chat**: In-game messaging system
- **Room-based Matchmaking**: Create or join rooms with codes
- **Responsive Design**: Works on desktop and mobile
- **Dynamic Probabilities**: Smart probability updates
- **Game State Management**: Server-authoritative logic

## 🔧 Development

### Backend API Endpoints

- `GET /`: Health check
- `GET /create_room`: Create a new room and return room code
- `WebSocket /ws/{room_code}`: Real-time game communication

### WebSocket Message Types

**Client → Server:**
- `place_piece`: Place a piece during placement phase
- `reveal_piece`: Reveal a piece during reveal phase  
- `chat_message`: Send a chat message

**Server → Client:**
- `game_state`: Updated game state
- `player_joined`: New player joined room
- `player_left`: Player left room
- `chat_message`: Broadcast chat message
- `error`: Error message

### Game State Structure

```typescript
interface GameState {
  board: (string | null)[];
  probabilities: (readonly [number, number] | readonly [null, null])[];
  phase: 'placement' | 'reveal';
  current_turn: number;
  revealed_cells: boolean[];
  winner: string | null;
  game_over: boolean;
  player_id: number;
}
```

## 🐛 Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Ensure backend is running on port 8000
   - Check firewall settings
   - Verify room code is correct

2. **Room is Full**
   - Each room supports maximum 2 players
   - Create a new room or wait for a player to leave

3. **Build Errors**
   - Run `npm install` to ensure all dependencies are installed
   - Check Node.js and npm versions meet requirements

### Development Notes

- The backend uses in-memory storage (rooms reset on server restart)
- For production, consider adding Redis or database persistence
- WebSocket connections are automatically cleaned up on disconnect
- Game logic is server-authoritative to prevent cheating

## 📄 License

This project is for educational and demonstration purposes.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

---

Built with ❤️ using React, TypeScript, and FastAPI