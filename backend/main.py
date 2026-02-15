from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import random
import string
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import time
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Add CORS middleware
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for rooms and connections
rooms: Dict[str, dict] = {}
connections: Dict[str, List[WebSocket]] = {}

class Game:
    def __init__(self):
        self.board = [None] * 9  # 9 cells, None means empty
        self.hidden_symbols = self._generate_hidden_symbols()
        self.probabilities = self._generate_probabilities()
        self.phase = "placement"  # "placement" or "reveal"
        self.current_turn = 0  # 0 or 1 for player index
        self.placed_pieces = 1  # Start with 1 because center is auto-placed
        self.revealed_cells = [False] * 9
        self.winner = None
        self.game_over = False
        self.play_again_votes = [False, False]  # Track play again votes
        self.turn_start_time = None  # Don't start timer until 2 players join
        self.turn_timeout = 30  # 30 seconds per turn
        
        # Auto-place center piece at start (but don't reveal it)
        self.board[4] = "placed"
        
    def _generate_hidden_symbols(self) -> List[str]:
        """Generate the hidden symbol distribution (5 of one, 4 of the other)"""
        # Randomly decide which symbol gets 5
        symbols = ['X', 'O']
        majority_symbol = random.choice(symbols)
        minority_symbol = 'O' if majority_symbol == 'X' else 'X'
        
        # Create the distribution
        symbol_list = [majority_symbol] * 5 + [minority_symbol] * 4
        random.shuffle(symbol_list)
        return symbol_list
    
    def _generate_probabilities(self) -> List[tuple]:
        """Generate probability pairs for each cell"""
        probabilities = []
        for i in range(9):
            # Generate probabilities biased toward actual symbol
            actual_symbol = self.hidden_symbols[i]
            if actual_symbol == 'X':
                # X is the actual symbol, so first probability is higher
                prob1 = random.randint(60, 95)
                prob2 = 100 - prob1
            else:
                # O is the actual symbol, so second probability is higher
                prob2 = random.randint(60, 95)
                prob1 = 100 - prob2
            probabilities.append((prob1, prob2))
        return probabilities
    
    def reset_turn_timer(self):
        """Reset the turn timer when turn changes"""
        if self.turn_start_time is not None:  # Only reset if timer was already started
            self.turn_start_time = time.time()
    
    def get_turn_time_remaining(self) -> int:
        """Get remaining time for current turn in seconds"""
        if self.turn_start_time is None:
            return 0  # Timer not started yet
        elapsed = time.time() - self.turn_start_time
        remaining = max(0, self.turn_timeout - int(elapsed))
        return remaining
    
    def is_turn_expired(self) -> bool:
        """Check if current turn has timed out"""
        return self.turn_start_time is not None and self.get_turn_time_remaining() <= 0
    
    def handle_turn_timeout(self):
        """Handle turn timeout by switching to next player"""
        if not self.game_over and self.is_turn_expired():
            # Switch to next player
            self.current_turn = 1 - self.current_turn
            self.reset_turn_timer()
            return True
        return False
    
    def start_timer(self):
        """Start the turn timer for the first time"""
        if self.turn_start_time is None:
            self.turn_start_time = time.time()
    
    def stop_timer(self):
        """Stop the turn timer (when players leave)"""
        self.turn_start_time = None

    def place_piece(self, position: int) -> bool:
        """Place a piece during placement phase"""
        if self.phase != "placement" or self.board[position] is not None or position == 4:
            return False
        
        self.board[position] = "placed"
        self.placed_pieces += 1
        
        # Transition to reveal phase when all pieces are placed
        if self.placed_pieces == 9:
            self.phase = "reveal"
            self.current_turn = 0  # Reset turn for reveal phase
            self.reset_turn_timer()  # Reset timer for reveal phase
        
        return True
    
    def reveal_piece(self, position: int) -> bool:
        """Reveal a piece during reveal phase"""
        if (self.phase != "reveal" or 
            self.board[position] is None or 
            self.revealed_cells[position]):
            return False
        
        self.revealed_cells[position] = True
        revealed_symbol = self.hidden_symbols[position]
        self.board[position] = revealed_symbol
        
        # Update probabilities for remaining hidden pieces
        self._update_probabilities_after_reveal(revealed_symbol)
        
        # Check for win condition
        self._check_win_condition()
        
        # Check for draw (all revealed, no winner)
        if all(self.revealed_cells) and not self.winner:
            self.game_over = True
        
        # If game is over, reveal all pieces
        if self.game_over:
            self._reveal_all_pieces()
        
        return True
    
    def _update_probabilities_after_reveal(self, revealed_symbol: str):
        """Update probabilities based on revealed information"""
        # Count remaining symbols
        remaining_x = sum(1 for i, symbol in enumerate(self.hidden_symbols) 
                         if not self.revealed_cells[i] and symbol == 'X')
        remaining_o = sum(1 for i, symbol in enumerate(self.hidden_symbols) 
                         if not self.revealed_cells[i] and symbol == 'O')
        
        total_remaining = remaining_x + remaining_o
        
        if total_remaining == 0:
            return
        
        # Update probabilities for unrevealed pieces
        for i in range(9):
            if not self.revealed_cells[i]:
                actual_symbol = self.hidden_symbols[i]
                if actual_symbol == 'X':
                    # This piece is actually X
                    x_prob = max(10, min(90, int((remaining_x / total_remaining) * 100) + random.randint(-15, 15)))
                    o_prob = 100 - x_prob
                else:
                    # This piece is actually O
                    o_prob = max(10, min(90, int((remaining_o / total_remaining) * 100) + random.randint(-15, 15)))
                    x_prob = 100 - o_prob
                
                self.probabilities[i] = (x_prob, o_prob)
    
    def _check_win_condition(self):
        """Check if there's a winner"""
        win_patterns = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
            [0, 4, 8], [2, 4, 6]  # diagonals
        ]
        
        for pattern in win_patterns:
            symbols = [self.board[i] for i in pattern]
            if (all(self.revealed_cells[i] for i in pattern) and 
                len(set(symbols)) == 1 and symbols[0] in ['X', 'O']):
                self.winner = symbols[0]
                self.game_over = True
                return
    
    def _reveal_all_pieces(self):
        """Reveal all pieces when game ends"""
        for i in range(9):
            if not self.revealed_cells[i]:
                self.revealed_cells[i] = True
                self.board[i] = self.hidden_symbols[i]
    
    def reset_game(self):
        """Reset game for play again"""
        self.__init__()
    
    def vote_play_again(self, player_id: int) -> bool:
        """Vote to play again, returns True if both players voted"""
        self.play_again_votes[player_id] = True
        return all(self.play_again_votes)
    
    def get_state(self, player_id: int) -> dict:
        """Get game state for a specific player"""
        return {
            "board": self.board,
            "probabilities": self.probabilities,
            "phase": self.phase,
            "current_turn": self.current_turn,
            "revealed_cells": self.revealed_cells,
            "winner": self.winner,
            "game_over": self.game_over,
            "player_id": player_id,
            "play_again_votes": self.play_again_votes,
            "turn_time_remaining": self.get_turn_time_remaining() if self.turn_start_time is not None else None,
            "turn_timeout": self.turn_timeout
        }

def generate_room_code() -> str:
    """Generate a unique 6-character room code"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if code not in rooms:
            return code

@app.websocket("/ws/{room_code}")
async def websocket_endpoint(websocket: WebSocket, room_code: str):
    await websocket.accept()
    
    # Wait for join message with player name
    try:
        join_message = await websocket.receive_json()
        if join_message.get("type") != "join":
            await websocket.send_json({
                "type": "error",
                "message": "Expected join message"
            })
            await websocket.close()
            return
        
        player_name = join_message.get("player_name", "Anonymous")
    except:
        await websocket.send_json({
            "type": "error",
            "message": "Invalid join message"
        })
        await websocket.close()
        return
    
    # Initialize room if it doesn't exist
    if room_code not in rooms:
        rooms[room_code] = {
            "players": [],
            "game": Game(),
            "chat_history": []
        }
        connections[room_code] = []
    
    # Check if room is full
    if len(rooms[room_code]["players"]) >= 2:
        await websocket.send_json({
            "type": "error",
            "message": "Room is full"
        })
        await websocket.close()
        return
    
    # Add player to room
    player_id = len(rooms[room_code]["players"])
    rooms[room_code]["players"].append({
        "id": player_id,
        "name": player_name,
        "websocket": websocket
    })
    connections[room_code].append(websocket)
    
    # Get game instance
    game = rooms[room_code]["game"]
    
    # Start timer if this is the second player
    if len(rooms[room_code]["players"]) == 2:
        game.start_timer()
    
    # Send initial game state
    await websocket.send_json({
        "type": "game_state",
        "data": game.get_state(player_id),
        "room_info": {
            "code": room_code,
            "players": [{"id": p["id"], "name": p["name"]} for p in rooms[room_code]["players"]],
            "waiting_for_player": len(rooms[room_code]["players"]) < 2
        }
    })
    
    # Broadcast to all players that someone joined
    await broadcast_to_room(room_code, {
        "type": "player_joined",
        "player": {"id": player_id, "name": player_name},
        "room_info": {
            "code": room_code,
            "players": [{"id": p["id"], "name": p["name"]} for p in rooms[room_code]["players"]],
            "waiting_for_player": len(rooms[room_code]["players"]) < 2
        }
    })
    
    try:
        async for message in websocket.iter_json():
            await handle_message(room_code, player_id, message)
    
    except WebSocketDisconnect:
        pass
    except:
        pass
    finally:
        # Handle player disconnect
        if room_code in rooms:
            # Stop timer if player count drops below 2
            if len(rooms[room_code]["players"]) >= 2:
                rooms[room_code]["game"].stop_timer()
            
            # Remove player from room
            rooms[room_code]["players"] = [p for p in rooms[room_code]["players"] if p["id"] != player_id]
            connections[room_code] = [conn for conn in connections[room_code] if conn != websocket]
            
            # If there are remaining players, notify them and close the room
            if rooms[room_code]["players"]:
                await broadcast_to_room(room_code, {
                    "type": "room_closed",
                    "message": f"{player_name} has left the game. Returning to lobby."
                })
                # Close all remaining connections
                for ws in connections[room_code]:
                    try:
                        await ws.close()
                    except:
                        pass
            
            # Clean up room
            if room_code in rooms:
                del rooms[room_code]
            if room_code in connections:
                del connections[room_code]

async def handle_message(room_code: str, player_id: int, message: dict):
    """Handle incoming WebSocket messages"""
    if room_code not in rooms or len(rooms[room_code]["players"]) < 2:
        return  # Don't process game actions until 2 players
        
    game = rooms[room_code]["game"]
    msg_type = message.get("type")
    
    if msg_type == "place_piece":
        position = message.get("position")
        if game.current_turn == player_id and game.place_piece(position):
            game.current_turn = 1 - game.current_turn  # Switch turns
            game.reset_turn_timer()  # Reset timer for new turn
            
            # Broadcast updated game state
            await broadcast_game_state(room_code)
    
    elif msg_type == "reveal_piece":
        position = message.get("position")
        if game.current_turn == player_id and game.reveal_piece(position):
            game.current_turn = 1 - game.current_turn  # Switch turns
            game.reset_turn_timer()  # Reset timer for new turn
            
            # Broadcast updated game state
            await broadcast_game_state(room_code)
    
    elif msg_type == "chat_message":
        player_name = next((p["name"] for p in rooms[room_code]["players"] if p["id"] == player_id), f"Player {player_id + 1}")
        chat_msg = {
            "type": "chat_message",
            "player_id": player_id,
            "player_name": player_name,
            "message": message.get("message", ""),
            "timestamp": datetime.now().isoformat()
        }
        rooms[room_code]["chat_history"].append(chat_msg)
        await broadcast_to_room(room_code, chat_msg)
    
    elif msg_type == "play_again":
        if game.vote_play_again(player_id):
            # Both players voted to play again, reset game
            game.reset_game()
            await broadcast_game_state(room_code)
            await broadcast_to_room(room_code, {
                "type": "game_reset",
                "message": "New game started!"
            })
        else:
            # Broadcast that this player wants to play again
            await broadcast_game_state(room_code)
            await broadcast_to_room(room_code, {
                "type": "play_again_vote",
                "player_id": player_id,
                "message": f"Player {player_id + 1} wants to play again. Waiting for other player..."
            })
async def broadcast_to_room(room_code: str, message: dict):
    """Broadcast a message to all players in a room"""
    if room_code not in connections:
        return
    
    disconnected = []
    for websocket in connections[room_code]:
        try:
            await websocket.send_json(message)
        except:
            disconnected.append(websocket)
    
    # Remove disconnected websockets
    for ws in disconnected:
        connections[room_code].remove(ws)

async def broadcast_game_state(room_code: str):
    """Broadcast current game state to all players"""
    if room_code not in rooms:
        return
        
    game = rooms[room_code]["game"]
    
    for i, player in enumerate(rooms[room_code]["players"]):
        try:
            await player["websocket"].send_json({
                "type": "game_state",
                "data": game.get_state(i),
                "room_info": {
                    "code": room_code,
                    "players": [{"id": p["id"], "name": p["name"]} for p in rooms[room_code]["players"]],
                    "waiting_for_player": len(rooms[room_code]["players"]) < 2
                }
            })
        except:
            pass

@app.get("/")
async def get():
    return {"message": "Entropy TicTacToe Backend"}

@app.get("/create_room")
async def create_room():
    """Create a new room and return the room code"""
    room_code = generate_room_code()
    return {"room_code": room_code}

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(timer_update_loop())

async def timer_update_loop():
    """Periodically update turn timers for all active games"""
    while True:
        await asyncio.sleep(1)  # Update every second
        
        for room_code, room_data in rooms.items():
            game = room_data["game"]
            
            if (game.turn_start_time is not None and 
                not game.game_over and 
                len(room_data["players"]) == 2):
                
                remaining_time = game.get_turn_time_remaining()
                
                # Check if time's up
                if remaining_time <= 0:
                    # Handle timeout
                    timed_out = game.handle_turn_timeout()
                    if timed_out:
                        # Broadcast timeout message
                        for player in room_data["players"]:
                            try:
                                await player["websocket"].send_json({
                                    "type": "timeout",
                                    "data": {
                                        "message": f"Turn timeout! Player {2 - game.current_turn} ran out of time."
                                    }
                                })
                            except:
                                pass
                        
                        # Broadcast updated game state
                        await broadcast_game_state(room_code)
                else:
                    # Send periodic updates
                    await broadcast_game_state(room_code)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)