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
from vs_ai.ai_player import EntropyTicTacToeAI

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
    def __init__(self, ai_mode=False, ai_player_id=None, ai_difficulty="expert"):
        self.board = [None] * 9  # 9 cells, None means empty
        self.hidden_symbols = self._generate_hidden_symbols()
        # Randomly decide if first number shows X or O probability
        self.first_number_is_x = random.choice([True, False])
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
        self.last_monty_position = None  # Store Monty Hall position for choice
        self.player_turn_counts = [0, 0]  # Track turn counts for each player
        self.monty_hall_state = None  # Track active Monty Hall state
        
        # AI settings
        self.ai_mode = ai_mode
        self.ai_player_id = ai_player_id
        self.ai_player = None
        if ai_mode and ai_player_id is not None:
            self.ai_player = EntropyTicTacToeAI(ai_player_id, ai_difficulty)
        
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
                # X is the actual symbol, so X probability is higher
                x_prob = random.randint(60, 95)
                o_prob = 100 - x_prob
            else:
                # O is the actual symbol, so O probability is higher
                o_prob = random.randint(60, 95)
                x_prob = 100 - o_prob
            
            # Randomly arrange which probability comes first based on game setting
            if self.first_number_is_x:
                probabilities.append((x_prob, o_prob))
            else:
                probabilities.append((o_prob, x_prob))
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
    
    def reveal_piece(self, position: int, player_id: int = None) -> dict:
        """Reveal a piece during reveal phase with Monty Hall mechanism"""
        if (self.phase != "reveal" or 
            self.board[position] is None or 
            self.revealed_cells[position]):
            return {"success": False, "error": "Invalid reveal"}
        
        # If we're in active Monty Hall state, handle the choice
        if self.monty_hall_state and self.monty_hall_state["player_id"] == player_id:
            if position == self.monty_hall_state["original_position"]:
                # Player clicked their original tile - private reveal
                result = self._complete_private_reveal(position)
                self.monty_hall_state = None  # Clear Monty Hall state
                return result
            elif position == self.monty_hall_state["monty_position"]:
                # Player clicked Monty Hall tile - public reveal
                result = self._complete_public_reveal(position)
                self.monty_hall_state = None  # Clear Monty Hall state
                return result
            else:
                return {"success": False, "error": "Invalid choice during Monty Hall"}
        
        # Increment player's turn count
        if player_id is not None:
            self.player_turn_counts[player_id] += 1
        
        # Store original choice
        original_symbol = self.hidden_symbols[position]
        
        # Check if this is player's 2nd, 4th, 6th turn etc. (every even turn)
        should_trigger_monty = (player_id is not None and 
                               self.player_turn_counts[player_id] % 2 == 0)
        
        if should_trigger_monty:
            # Trigger Monty Hall on every 2nd turn
            monty_hall_result = self._trigger_monty_hall(position, original_symbol)
            
            if monty_hall_result["triggered"]:
                # Store Monty Hall state
                self.monty_hall_state = {
                    "player_id": player_id,
                    "original_position": position,
                    "monty_position": monty_hall_result["revealed_position"],
                    "monty_symbol": monty_hall_result["revealed_symbol"]
                }
                
                return {
                    "success": True,
                    "monty_hall_active": True,
                    "original_position": position,
                    "monty_position": monty_hall_result["revealed_position"],
                    "monty_symbol": monty_hall_result["revealed_symbol"],
                    "piece_type": monty_hall_result["piece_type"],
                    "strategy_hint": monty_hall_result["strategy_hint"]
                }
        
        # Standard reveal (no Monty Hall or fallback)
        return self._complete_public_reveal(position)
    
    def make_monty_hall_choice(self, original_position: int, choice: str) -> dict:
        """Handle player's choice in Monty Hall scenario"""
        if choice == "original":
            # Player chose their original tile - they get private knowledge
            # Tile stays hidden to opponent but player knows what it contains
            original_symbol = self.hidden_symbols[original_position]
            return {
                "success": True,
                "monty_hall": False,
                "private_reveal": True,
                "position": original_position,
                "symbol": original_symbol,
                "message": f"You privately learned this tile contains {original_symbol}"
            }
        elif choice == "monty":
            # Player chose Monty Hall tile - reveal it publicly to both players
            monty_position = self.last_monty_position  # We need to store this
            monty_symbol = self.hidden_symbols[monty_position]
            
            # Actually reveal the Monty Hall tile publicly
            self.revealed_cells[monty_position] = True
            self.board[monty_position] = monty_symbol
            
            # Update probabilities
            self._update_probabilities_after_reveal(monty_symbol)
            
            # Check for win condition
            self._check_win_condition()
            
            # Check for draw
            if all(self.revealed_cells) and not self.winner:
                self.game_over = True
                
            # If game is over, reveal all pieces
            if self.game_over:
                self._reveal_all_pieces()
            
            return {
                "success": True,
                "monty_hall": False,
                "public_reveal": True,
                "position": monty_position,
                "symbol": monty_symbol,
                "message": f"Monty Hall tile revealed: {monty_symbol}"
            }
        
    def _trigger_monty_hall(self, chosen_position: int, chosen_symbol: str) -> dict:
        """Trigger Monty Hall mechanism - returns info but doesn't reveal publicly"""
        # Define all possible lines
        lines = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
            [0, 4, 8], [2, 4, 6]  # diagonals
        ]
        
        # Find lines containing the chosen position and try all of them
        relevant_lines = [line for line in lines if chosen_position in line]
        
        if not relevant_lines:
            return {"triggered": False}
        
        # Try each line until we find candidates
        all_candidates = []
        for line in relevant_lines:
            candidates = [pos for pos in line 
                         if pos != chosen_position and not self.revealed_cells[pos]]
            all_candidates.extend(candidates)
        
        # Remove duplicates
        all_candidates = list(set(all_candidates))
        
        if not all_candidates:
            return {"triggered": False}
        
        # Apply 80/20 rule for symbol selection
        opposite_symbol = 'O' if chosen_symbol == 'X' else 'X'
        
        # Separate candidates by symbol
        opposite_candidates = [pos for pos in all_candidates 
                             if self.hidden_symbols[pos] == opposite_symbol]
        same_candidates = [pos for pos in all_candidates 
                          if self.hidden_symbols[pos] == chosen_symbol]
        
        # 80% chance to reveal opposite, 20% chance to reveal same
        if random.randint(1, 100) <= 80 and opposite_candidates:
            reveal_position = random.choice(opposite_candidates)
        elif same_candidates:
            reveal_position = random.choice(same_candidates)
        elif opposite_candidates:
            reveal_position = random.choice(opposite_candidates)
        else:
            # Fallback: just pick any available candidate
            reveal_position = random.choice(all_candidates)
        
        # DON'T actually reveal the piece publicly - just return the info
        revealed_symbol = self.hidden_symbols[reveal_position]
        
        # Store the Monty Hall position for later choice
        self.last_monty_position = reveal_position
        
        # Determine if this is beneficial or detrimental for the player
        is_beneficial = revealed_symbol != chosen_symbol
        piece_type = "winning" if is_beneficial else "losing"
        strategy_hint = "This makes switching more favorable" if is_beneficial else "This makes staying more favorable"
        
        return {
            "triggered": True,
            "revealed_position": reveal_position,
            "revealed_symbol": revealed_symbol,
            "piece_type": piece_type,
            "strategy_hint": strategy_hint
        }
    
    def _complete_private_reveal(self, position: int) -> dict:
        """Complete reveal of original tile (public reveal, but player had private info to make choice)"""
        # Actually reveal the tile publicly - both players see it
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
        
        return {
            "success": True,
            "public_reveal": True,  # Changed to public_reveal
            "position": position,
            "symbol": revealed_symbol,
            "message": f"You chose your original tile: {revealed_symbol}"
        }
    
    def _complete_public_reveal(self, position: int) -> dict:
        """Complete a public reveal (tile gets revealed to everyone)"""
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
        
        return {
            "success": True,
            "public_reveal": True,
            "position": position,
            "symbol": revealed_symbol
        }
    
    def _update_probabilities_after_reveal(self, revealed_symbol: str):
        """Update probabilities using Monty Hall-style logic"""
        # Get lines containing the last revealed piece
        last_revealed = next(i for i in range(9) if self.revealed_cells[i] and self.board[i] == revealed_symbol)
        
        # Define all possible lines (rows, columns, diagonals)
        lines = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
            [0, 4, 8], [2, 4, 6]  # diagonals
        ]
        
        # Count remaining symbols globally
        remaining_x = sum(1 for i, symbol in enumerate(self.hidden_symbols) 
                         if not self.revealed_cells[i] and symbol == 'X')
        remaining_o = sum(1 for i, symbol in enumerate(self.hidden_symbols) 
                         if not self.revealed_cells[i] and symbol == 'O')
        
        total_remaining = remaining_x + remaining_o
        if total_remaining == 0:
            return
            
        # Base probabilities
        base_x_prob = remaining_x / total_remaining
        base_o_prob = remaining_o / total_remaining
        
        # Apply Monty Hall logic: pieces in same lines as revealed pieces get probability boosts
        for i in range(9):
            if not self.revealed_cells[i]:
                # Start with base probability
                x_prob = base_x_prob
                o_prob = base_o_prob
                
                # Check if this cell shares lines with revealed pieces
                monty_hall_boost = 0
                for line in lines:
                    if i in line:
                        # Count revealed pieces in this line
                        revealed_in_line = sum(1 for pos in line if self.revealed_cells[pos])
                        same_symbol_in_line = sum(1 for pos in line 
                                                if self.revealed_cells[pos] and self.board[pos] == revealed_symbol)
                        
                        if revealed_in_line > 0:
                            # Monty Hall effect: knowing one door increases odds on remaining doors
                            if same_symbol_in_line > 0:
                                # If revealed symbol appears in this line, boost that symbol's probability
                                if revealed_symbol == 'X':
                                    monty_hall_boost += 0.15 * (same_symbol_in_line / 3)
                                else:
                                    monty_hall_boost -= 0.15 * (same_symbol_in_line / 3)
                
                # Apply the boost
                if revealed_symbol == 'X':
                    x_prob = min(0.9, x_prob + monty_hall_boost)
                    o_prob = 1.0 - x_prob
                else:
                    o_prob = min(0.9, o_prob + monty_hall_boost)
                    x_prob = 1.0 - o_prob
                
                # Add bias toward the actual symbol in this cell (like placement phase)
                actual_symbol = self.hidden_symbols[i]
                if actual_symbol == 'X':
                    # This cell actually contains X, boost X probability
                    symbol_bias = random.randint(10, 25) / 100.0  # 10-25% bias
                    x_prob = min(0.9, x_prob + symbol_bias)
                    o_prob = 1.0 - x_prob
                else:
                    # This cell actually contains O, boost O probability  
                    symbol_bias = random.randint(10, 25) / 100.0  # 10-25% bias
                    o_prob = min(0.9, o_prob + symbol_bias)
                    x_prob = 1.0 - o_prob
                
                # Add small random noise to maintain some uncertainty
                noise = random.randint(-5, 5) / 100.0
                x_prob = max(0.1, min(0.9, x_prob + noise))
                o_prob = 1.0 - x_prob
                
                # Arrange probabilities based on game's random assignment
                if self.first_number_is_x:
                    self.probabilities[i] = (int(x_prob * 100), int(o_prob * 100))
                else:
                    self.probabilities[i] = (int(o_prob * 100), int(x_prob * 100))
    
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
        ai_mode = getattr(self, 'ai_mode', False)
        ai_player_id = getattr(self, 'ai_player_id', None)
        ai_difficulty = getattr(self, 'ai_player', None).difficulty if hasattr(self, 'ai_player') and self.ai_player else 'expert'
        self.__init__(ai_mode=ai_mode, ai_player_id=ai_player_id, ai_difficulty=ai_difficulty)
    
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
            "turn_timeout": self.turn_timeout,
            "monty_hall_state": self.monty_hall_state if self.monty_hall_state and self.monty_hall_state["player_id"] == player_id else None
        }

class AIOpponent:
    """Algorithmic AI opponent for single-player mode"""
    
    def __init__(self, difficulty="expert"):
        self.difficulty = difficulty
        self.player_id = 1  # AI is always player 1
    
    def choose_placement(self, game) -> int:
        """Algorithm to choose placement position"""
        available_positions = [i for i in range(9) if game.board[i] is None and i != 4]
        
        if not available_positions:
            return None
            
        if self.difficulty == "easy":
            return random.choice(available_positions)
        
        # Medium/Hard: Strategic placement
        scores = []
        for pos in available_positions:
            score = self._evaluate_placement_position(pos, game)
            scores.append((pos, score))
        
        # Sort by score and add some randomness for medium difficulty
        scores.sort(key=lambda x: x[1], reverse=True)
        
        if self.difficulty == "medium" and len(scores) > 1:
            # Sometimes pick second best move
            if random.random() < 0.3:
                return scores[1][0] if len(scores) > 1 else scores[0][0]
        
        return scores[0][0]
    
    def choose_reveal(self, game) -> int:
        """Algorithm to choose reveal position"""
        available_positions = [i for i in range(9) if game.board[i] is not None and not game.revealed_cells[i]]
        
        if not available_positions:
            return None
            
        if self.difficulty == "easy":
            return random.choice(available_positions)
        
        # Medium/Hard: Strategic reveal based on probabilities
        scores = []
        for pos in available_positions:
            score = self._evaluate_reveal_position(pos, game)
            scores.append((pos, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        if self.difficulty == "medium" and len(scores) > 1:
            # Sometimes pick second best move
            if random.random() < 0.4:
                return scores[1][0] if len(scores) > 1 else scores[0][0]
        
        return scores[0][0]
    
    def _evaluate_placement_position(self, position, game) -> float:
        """Evaluate placement position value"""
        score = 0
        
        # Strategic positions (corners and center area)
        strategic_positions = [0, 2, 6, 8, 1, 3, 5, 7]  # corners first, then edges
        if position in strategic_positions[:4]:  # corners
            score += 30
        elif position in strategic_positions[4:]:  # edges
            score += 20
        
        # Check if position blocks or creates potential lines
        lines = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
            [0, 4, 8], [2, 4, 6]  # diagonals
        ]
        
        for line in lines:
            if position in line:
                line_pieces = sum(1 for pos in line if game.board[pos] is not None)
                if line_pieces == 1:  # One piece in line, good to add another
                    score += 15
                elif line_pieces == 2:  # Two pieces, very important position
                    score += 50
        
        return score + random.random() * 5  # Add small random factor
    
    def _evaluate_reveal_position(self, position, game) -> float:
        """Evaluate reveal position value based on probabilities"""
        score = 0
        prob1, prob2 = game.probabilities[position]
        
        # Prefer higher probability positions
        max_prob = max(prob1, prob2)
        score += max_prob
        
        # Check if revealing could create winning lines
        lines = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
            [0, 4, 8], [2, 4, 6]  # diagonals
        ]
        
        for line in lines:
            if position in line:
                revealed_in_line = sum(1 for pos in line if game.revealed_cells[pos])
                if revealed_in_line >= 1:  # Already have revelations in this line
                    score += 25
        
        return score + random.random() * 10  # Add random factor

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
    
    # Check if this is an AI room
    is_ai_room = rooms[room_code].get("ai_mode", False)
    
    # Check if room is full
    max_players = 1 if is_ai_room else 2
    if len(rooms[room_code]["players"]) >= max_players:
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
    
    # Add AI player if this is an AI room and human just joined
    if is_ai_room and len(rooms[room_code]["players"]) == 1:
        ai_player_id = rooms[room_code]["ai_player_id"]
        ai_difficulty = rooms[room_code]["ai_difficulty"]
        rooms[room_code]["players"].append({
            "id": ai_player_id,
            "name": f"AI ({ai_difficulty.title()})",
            "websocket": None,  # AI doesn't have websocket
            "is_ai": True
        })
    
    # Get game instance
    game = rooms[room_code]["game"]
    
    # Start timer if we have enough players (2 for normal, 1+AI for AI mode)
    required_players = 1 if is_ai_room else 2
    if len(rooms[room_code]["players"]) >= required_players:
        game.start_timer()
    
    # Send initial game state
    await websocket.send_json({
        "type": "game_state",
        "data": game.get_state(player_id),
        "room_info": {
            "code": room_code,
            "players": [{"id": p["id"], "name": p["name"], "is_ai": p.get("is_ai", False)} for p in rooms[room_code]["players"]],
            "waiting_for_player": len(rooms[room_code]["players"]) < (1 if is_ai_room else 2),
            "ai_mode": is_ai_room
        }
    })
    
    # Broadcast to all players that someone joined
    await broadcast_to_room(room_code, {
        "type": "player_joined",
        "player": {"id": player_id, "name": player_name},
        "room_info": {
            "code": room_code,
            "players": [{"id": p["id"], "name": p["name"], "is_ai": p.get("is_ai", False)} for p in rooms[room_code]["players"]],
            "waiting_for_player": len(rooms[room_code]["players"]) < (1 if is_ai_room else 2),
            "ai_mode": is_ai_room
        }
    })
    
    # Start AI turn if needed
    if is_ai_room and game.current_turn == game.ai_player_id:
        asyncio.create_task(handle_ai_turn(room_code))
    
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
    if room_code not in rooms:
        return
        
    # Check if room has enough players
    is_ai_room = rooms[room_code].get("ai_mode", False)
    required_players = 1 if is_ai_room else 2
    
    if len(rooms[room_code]["players"]) < required_players:
        return  # Don't process game actions until enough players
        
    game = rooms[room_code]["game"]
    msg_type = message.get("type")
    
    if msg_type == "place_piece":
        position = message.get("position")
        if game.current_turn == player_id and game.place_piece(position):
            await handle_piece_placed(room_code)
    
    elif msg_type == "reveal_piece":
        position = message.get("position")
        if game.current_turn == player_id:
            await handle_piece_revealed(room_code, player_id, position)
    
    elif msg_type == "chat_message":
        if not is_ai_room:  # Only allow chat in human vs human games
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
        print(f"Play again request from player {player_id} in room {room_code}")
        print(f"Is AI room: {is_ai_room}")
        
        # In AI mode, immediately restart the game when human clicks play again
        if is_ai_room:
            print("AI mode: Immediately restarting game")
            try:
                # Reset game immediately without any voting
                print("Step 1: Calling reset_game()")
                game.reset_game()
                print("Step 2: Calling start_timer()")
                # Restart the timer
                game.start_timer()
                print("Step 3: Broadcasting game state")
                await broadcast_game_state(room_code)
                print("Step 4: Broadcasting game reset message")
                await broadcast_to_room(room_code, {
                    "type": "game_reset",
                    "message": "New game started!"
                })
                
                print("Step 5: Checking AI turn")
                # Start AI turn if needed
                if game.current_turn == game.ai_player_id:
                    print(f"Starting AI turn for player {game.ai_player_id}")
                    asyncio.create_task(handle_ai_turn(room_code))
                else:
                    print(f"Human turn - current turn: {game.current_turn}")
                print("Play again complete!")
            except Exception as e:
                print(f"Error in play again: {e}")
                import traceback
                traceback.print_exc()
        else:
            # Regular 2-player room logic with voting
            if game.vote_play_again(player_id):
                # Both players voted to play again, reset game
                game.reset_game()
                # Restart the timer
                game.start_timer()
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
async def handle_piece_placed(room_code: str):
    """Handle after a piece is placed"""
    if room_code not in rooms:
        return
        
    game = rooms[room_code]["game"]
    is_ai_room = rooms[room_code].get("ai_mode", False)
    
    # Switch turns
    game.current_turn = 1 - game.current_turn
    game.reset_turn_timer()
    
    # Broadcast updated game state
    await broadcast_game_state(room_code)
    
    # Handle AI turn if needed
    if is_ai_room and game.current_turn == game.ai_player_id:
        asyncio.create_task(handle_ai_turn(room_code))

async def handle_piece_revealed(room_code: str, player_id: int, position: int):
    """Handle after a piece is revealed"""
    if room_code not in rooms:
        return
        
    game = rooms[room_code]["game"]
    is_ai_room = rooms[room_code].get("ai_mode", False)
    
    result = game.reveal_piece(position, player_id)
    if result["success"]:
        if result.get("monty_hall_active"):
            # Monty Hall is now active
            if player_id == game.ai_player_id:
                # AI needs to make Monty Hall choice
                asyncio.create_task(handle_ai_monty_hall_choice(room_code, result))
            else:
                # Human player - show choice interface
                player_ws = next((p["websocket"] for p in rooms[room_code]["players"] if p["id"] == player_id), None)
                if player_ws:
                    await player_ws.send_json({
                        "type": "monty_hall_info",
                        "monty_position": result["monty_position"],
                        "monty_symbol": result["monty_symbol"],
                        "piece_type": result["piece_type"],
                        "strategy_hint": result["strategy_hint"]
                    })
            # Broadcast game state to show visual indicators
            await broadcast_game_state(room_code)
        elif result.get("private_reveal"):
            # Original tile chosen - public reveal but send notification to current player only
            if not (player_id == game.ai_player_id):  # Don't send to AI
                player_ws = next((p["websocket"] for p in rooms[room_code]["players"] if p["id"] == player_id), None)
                if player_ws:
                    await player_ws.send_json({
                        "type": "choice_info", 
                        "message": result["message"]
                    })
            await finish_turn(room_code)
        elif result.get("public_reveal"):
            # Public reveal
            await finish_turn(room_code)

async def finish_turn(room_code: str):
    """Finish the current turn and switch to next player"""
    if room_code not in rooms:
        return
        
    game = rooms[room_code]["game"]
    is_ai_room = rooms[room_code].get("ai_mode", False)
    
    # Switch turns and broadcast
    game.current_turn = 1 - game.current_turn
    game.reset_turn_timer()
    await broadcast_game_state(room_code)
    
    # Handle AI turn if needed
    if is_ai_room and game.current_turn == game.ai_player_id and not game.game_over:
        asyncio.create_task(handle_ai_turn(room_code))

async def handle_ai_turn(room_code: str):
    """Handle AI making a move"""
    if room_code not in rooms:
        return
        
    game = rooms[room_code]["game"]
    is_ai_room = rooms[room_code].get("ai_mode", False)
    
    if not is_ai_room or game.current_turn != game.ai_player_id or game.game_over:
        return
    
    # Check if AI is in Monty Hall state (should be handled by separate function)
    if game.monty_hall_state and game.monty_hall_state["player_id"] == game.ai_player_id:
        return  # Monty Hall choice is handled separately
    
    try:
        # Get AI move
        game_state = game.get_state(game.ai_player_id)
        position = await game.ai_player.make_move(game_state, game)
        
        # Execute the move
        if game_state["phase"] == "placement":
            if game.place_piece(position):
                await handle_piece_placed(room_code)
        elif game_state["phase"] == "reveal":
            await handle_piece_revealed(room_code, game.ai_player_id, position)
            
    except Exception as e:
        print(f"AI turn error in room {room_code}: {e}")
        # On error, make random valid move
        valid_moves = get_valid_moves_for_game(game)
        if valid_moves:
            position = random.choice(valid_moves)
            
            game_state = game.get_state(game.ai_player_id)
            if game_state["phase"] == "placement":
                if game.place_piece(position):
                    await handle_piece_placed(room_code)
            elif game_state["phase"] == "reveal":
                await handle_piece_revealed(room_code, game.ai_player_id, position)

async def handle_ai_monty_hall_choice(room_code: str, monty_hall_result: dict):
    """Handle AI making a Monty Hall choice"""
    if room_code not in rooms:
        return
        
    game = rooms[room_code]["game"]
    
    try:
        # Get AI choice
        game_state = game.get_state(game.ai_player_id)
        choice = await game.ai_player.make_monty_hall_choice(game_state, game.monty_hall_state)
        
        # Execute the choice
        if choice == "original":
            # AI chose original tile
            result = game._complete_private_reveal(game.monty_hall_state["original_position"])
            game.monty_hall_state = None
            await finish_turn(room_code)
        elif choice == "monty":
            # AI chose Monty Hall tile
            result = game._complete_public_reveal(game.monty_hall_state["monty_position"])
            game.monty_hall_state = None
            await finish_turn(room_code)
            
    except Exception as e:
        print(f"AI Monty Hall error in room {room_code}: {e}")
        # Default to original choice on error
        result = game._complete_private_reveal(game.monty_hall_state["original_position"])
        game.monty_hall_state = None
        await finish_turn(room_code)

def get_valid_moves_for_game(game) -> List[int]:
    """Get valid moves for current game state"""
    valid_moves = []
    
    if game.phase == "placement":
        for i in range(9):
            if game.board[i] is None and i != 4:  # Can't place on center
                valid_moves.append(i)
    else:  # reveal phase
        for i in range(9):
            if game.board[i] == "placed" and not game.revealed_cells[i]:
                valid_moves.append(i)
    
    return valid_moves

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
    is_ai_room = rooms[room_code].get("ai_mode", False)
    
    for i, player in enumerate(rooms[room_code]["players"]):
        # Skip AI players (they don't have websockets)
        if player.get("is_ai", False) or not player.get("websocket"):
            continue
            
        try:
            await player["websocket"].send_json({
                "type": "game_state",
                "data": game.get_state(i),
                "room_info": {
                    "code": room_code,
                    "players": [{"id": p["id"], "name": p["name"], "is_ai": p.get("is_ai", False)} for p in rooms[room_code]["players"]],
                    "waiting_for_player": len(rooms[room_code]["players"]) < (1 if is_ai_room else 2),
                    "ai_mode": is_ai_room
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

@app.get("/create_ai_room")
async def create_ai_room(difficulty: str = "expert"):
    """Create a new room with AI opponent"""
    room_code = generate_room_code()
    
    # Validate difficulty
    if difficulty not in ["easy", "medium", "hard", "expert"]:
        difficulty = "expert"
    
    # Initialize room with AI
    ai_player_id = 1  # AI is always player 1
    rooms[room_code] = {
        "players": [],
        "game": Game(ai_mode=True, ai_player_id=ai_player_id, ai_difficulty=difficulty),
        "chat_history": [],
        "ai_mode": True,
        "ai_player_id": ai_player_id,
        "ai_difficulty": difficulty
    }
    connections[room_code] = []
    
    return {"room_code": room_code, "ai_mode": True, "difficulty": difficulty}

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