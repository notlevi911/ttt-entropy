import random
import asyncio
from typing import Dict, List, Tuple, Optional
import copy

class EntropyTicTacToeAI:
    def __init__(self, ai_player_id: int, difficulty: str = "medium"):
        """
        Initialize AI player for Entropy TicTacToe
        
        Args:
            ai_player_id: The player ID (0 or 1) for the AI
            difficulty: "easy", "medium", "hard", "expert"
        """
        self.ai_player_id = ai_player_id
        self.opponent_id = 1 - ai_player_id
        self.difficulty = difficulty
        
        # Difficulty settings
        self.depth_limits = {
            "easy": 2,
            "medium": 4, 
            "hard": 6,
            "expert": 8
        }
        
        self.randomness = {
            "easy": 0.3,      # 30% random moves
            "medium": 0.15,   # 15% random moves
            "hard": 0.05,     # 5% random moves
            "expert": 0.0     # No random moves
        }
        
        # Track revealed symbol patterns
        self.symbol_pattern_knowledge = None  # Will be learned during game
        
    async def make_move(self, game_state, game_instance) -> int:
        """
        Make an AI move based on current game state
        
        Returns:
            position (int): The position to place/reveal
        """
        # Add a small delay to make AI feel more natural
        delay = random.uniform(0.5, 2.0) if self.difficulty != "expert" else random.uniform(0.2, 0.8)
        await asyncio.sleep(delay)
        
        # Check for random move based on difficulty
        if random.random() < self.randomness[self.difficulty]:
            return self._make_random_move(game_state, game_instance)
        
        if game_state["phase"] == "placement":
            return self._make_placement_move(game_state, game_instance)
        else:  # reveal phase
            return self._make_reveal_move(game_state, game_instance)
    
    def _make_random_move(self, game_state, game_instance) -> int:
        """Make a random valid move"""
        valid_moves = self._get_valid_moves(game_state)
        return random.choice(valid_moves) if valid_moves else 0
    
    def _get_valid_moves(self, game_state) -> List[int]:
        """Get list of valid move positions"""
        valid_moves = []
        
        if game_state["phase"] == "placement":
            for i in range(9):
                if game_state["board"][i] is None and i != 4:  # Can't place on center (auto-placed)
                    valid_moves.append(i)
        else:  # reveal phase
            for i in range(9):
                if (game_state["board"][i] == "placed" and 
                    not game_state["revealed_cells"][i]):
                    valid_moves.append(i)
        
        return valid_moves
    
    def _make_placement_move(self, game_state, game_instance) -> int:
        """Make a strategic placement move using probability analysis"""
        valid_moves = self._get_valid_moves(game_state)
        if not valid_moves:
            return 0
        
        depth = self.depth_limits[self.difficulty]
        best_move = None
        best_score = float('-inf')
        
        for position in valid_moves:
            # Simulate the move
            simulated_state = self._simulate_placement(game_state, position)
            
            # Evaluate the position using minimax
            score = self._minimax_placement(
                simulated_state, 
                depth - 1, 
                False,  # Next move is opponent's
                float('-inf'),
                float('inf'),
                game_instance
            )
            
            if score > best_score:
                best_score = score
                best_move = position
        
        return best_move if best_move is not None else valid_moves[0]
    
    def _make_reveal_move(self, game_state, game_instance) -> int:
        """Make a strategic reveal move using game knowledge and probabilities"""
        valid_moves = self._get_valid_moves(game_state)
        if not valid_moves:
            return 0
        
        # First, update our knowledge about symbol patterns
        self._update_symbol_knowledge(game_state)
        
        depth = self.depth_limits[self.difficulty] 
        best_move = None
        best_score = float('-inf')
        
        for position in valid_moves:
            # Calculate expected value for revealing this position
            score = self._evaluate_reveal_position(position, game_state, game_instance)
            
            if score > best_score:
                best_score = score
                best_move = position
        
        return best_move if best_move is not None else valid_moves[0]
    
    def _simulate_placement(self, game_state, position: int) -> dict:
        """Simulate placing a piece at the given position"""
        simulated_state = copy.deepcopy(game_state)
        simulated_state["board"][position] = "placed"
        
        # Check if placement phase is complete
        placed_pieces = sum(1 for cell in simulated_state["board"] if cell is not None)
        if placed_pieces == 9:
            simulated_state["phase"] = "reveal"
            simulated_state["current_turn"] = 0  # Reset to player 0 for reveal phase
        else:
            simulated_state["current_turn"] = 1 - simulated_state["current_turn"]
        
        return simulated_state
    
    def _minimax_placement(self, game_state, depth: int, is_maximizing: bool, 
                          alpha: float, beta: float, game_instance) -> float:
        """Minimax algorithm adapted for placement phase"""
        if depth == 0 or self._is_placement_terminal(game_state):
            return self._evaluate_placement_position(game_state, game_instance)
        
        valid_moves = self._get_valid_moves(game_state)
        
        if is_maximizing:
            max_score = float('-inf')
            for position in valid_moves:
                simulated_state = self._simulate_placement(game_state, position)
                score = self._minimax_placement(simulated_state, depth - 1, False, alpha, beta, game_instance)
                max_score = max(max_score, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            return max_score
        else:
            min_score = float('inf')
            for position in valid_moves:
                simulated_state = self._simulate_placement(game_state, position)
                score = self._minimax_placement(simulated_state, depth - 1, True, alpha, beta, game_instance)
                min_score = min(min_score, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            return min_score
    
    def _evaluate_placement_position(self, game_state, game_instance) -> float:
        """Evaluate the strategic value of a placement position"""
        score = 0
        
        # Strategic position values (center is most valuable, corners next, edges least)
        position_values = {
            4: 10,  # Center
            0: 7, 2: 7, 6: 7, 8: 7,  # Corners
            1: 4, 3: 4, 5: 4, 7: 4   # Edges
        }
        
        # Add points for controlling strategic positions
        for i, cell in enumerate(game_state["board"]):
            if cell == "placed":
                score += position_values.get(i, 0)
        
        # Add points for potential line completion opportunities
        lines = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
            [0, 4, 8], [2, 4, 6]  # diagonals
        ]
        
        for line in lines:
            placed_in_line = sum(1 for pos in line if game_state["board"][pos] == "placed")
            empty_in_line = sum(1 for pos in line if game_state["board"][pos] is None)
            
            # Prefer lines with good potential for reveals
            if placed_in_line >= 2:
                score += placed_in_line * 3
        
        return score
    
    def _is_placement_terminal(self, game_state) -> bool:
        """Check if placement phase is complete"""
        return game_state["phase"] == "reveal"
    
    def _evaluate_reveal_position(self, position: int, game_state, game_instance) -> float:
        """Evaluate the value of revealing a position"""
        score = 0
        probabilities = game_state["probabilities"][position]
        
        if not probabilities or len(probabilities) != 2:
            return 0
        
        prob1, prob2 = probabilities
        
        # If we've identified the symbol pattern, use it
        if self.symbol_pattern_knowledge:
            ai_symbol_prob = self._get_ai_symbol_probability(position, game_state)
            
            # Strongly prefer high probability positions for our symbol
            if ai_symbol_prob > 70:
                score += 15
            elif ai_symbol_prob > 60:
                score += 10
            elif ai_symbol_prob < 30:
                score -= 10  # Avoid revealing opponent symbols
            elif ai_symbol_prob < 40:
                score -= 5
        else:
            # No pattern knowledge yet - use conservative strategy
            max_prob = max(prob1, prob2)
            score += max_prob * 0.1
        
        # Check for winning opportunities and threats
        score += self._evaluate_tactical_position(position, game_state)
        
        # Add randomness for lower difficulties
        if self.difficulty in ["easy", "medium"]:
            score += random.uniform(-2, 2)
        
        return score
    
    def _evaluate_tactical_position(self, position: int, game_state) -> float:
        """Evaluate tactical importance of a position (winning/blocking)"""
        score = 0
        lines = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
            [0, 4, 8], [2, 4, 6]  # diagonals
        ]
        
        for line in lines:
            if position in line:
                revealed_symbols = []
                unrevealed_count = 0
                
                for pos in line:
                    if game_state["revealed_cells"][pos]:
                        revealed_symbols.append(game_state["board"][pos])
                    elif game_state["board"][pos] == "placed":
                        unrevealed_count += 1
                
                # Check for potential wins/blocks
                if len(revealed_symbols) == 2 and unrevealed_count == 1:
                    if len(set(revealed_symbols)) == 1:  # Two same symbols
                        # This could be a winning/blocking move
                        score += 20
                
                # Value lines with revealed pieces (information value)
                if revealed_symbols:
                    score += len(revealed_symbols) * 2
        
        return score
    
    def _update_symbol_knowledge(self, game_state):
        """Learn the symbol pattern from revealed pieces"""
        if self.symbol_pattern_knowledge is not None:
            return  # Already learned
        
        # Look for revealed pieces to determine which probability number represents which symbol
        for i in range(9):
            if game_state["revealed_cells"][i]:
                revealed_symbol = game_state["board"][i]
                probabilities = game_state["probabilities"][i]
                
                if probabilities and len(probabilities) == 2:
                    prob1, prob2 = probabilities
                    
                    # Assume the higher probability was for the actual symbol
                    if prob1 > prob2:
                        self.symbol_pattern_knowledge = {
                            "first_number_is_x": revealed_symbol == 'X'
                        }
                    else:
                        self.symbol_pattern_knowledge = {
                            "first_number_is_x": revealed_symbol != 'X'
                        }
                    break
    
    def _get_ai_symbol_probability(self, position: int, game_state) -> float:
        """Get probability that the position contains AI's preferred symbol"""
        if not self.symbol_pattern_knowledge:
            return 50  # No knowledge yet
        
        probabilities = game_state["probabilities"][position]
        if not probabilities or len(probabilities) != 2:
            return 50
        
        prob1, prob2 = probabilities
        
        # Count revealed symbols to determine which symbol AI should prefer
        revealed_x = sum(1 for i in range(9) 
                        if game_state["revealed_cells"][i] and game_state["board"][i] == 'X')
        revealed_o = sum(1 for i in range(9) 
                        if game_state["revealed_cells"][i] and game_state["board"][i] == 'O')
        
        # AI should prefer the symbol that appears to be in majority
        # or if unknown, prefer X if AI is player 0, O if player 1
        if revealed_x > revealed_o:
            preferred_symbol = 'X'
        elif revealed_o > revealed_x:
            preferred_symbol = 'O' 
        else:
            # Default preference based on player ID
            preferred_symbol = 'X' if self.ai_player_id == 0 else 'O'
        
        # Return the probability for AI's preferred symbol
        if self.symbol_pattern_knowledge["first_number_is_x"]:
            return prob1 if preferred_symbol == 'X' else prob2
        else:
            return prob2 if preferred_symbol == 'X' else prob1
    
    async def make_monty_hall_choice(self, game_state, monty_hall_state) -> str:
        """Make Monty Hall choice decision"""
        # Add thinking delay
        delay = random.uniform(1.0, 3.0) if self.difficulty != "expert" else random.uniform(0.5, 1.5)
        await asyncio.sleep(delay)
        
        # Strategic Monty Hall decision
        original_pos = monty_hall_state["original_position"]
        monty_pos = monty_hall_state["monty_position"]
        monty_symbol = monty_hall_state["monty_symbol"]
        
        # Get AI's symbol preference
        revealed_x = sum(1 for i in range(9) 
                        if game_state["revealed_cells"][i] and game_state["board"][i] == 'X')
        revealed_o = sum(1 for i in range(9) 
                        if game_state["revealed_cells"][i] and game_state["board"][i] == 'O')
        
        # Determine what AI wants
        if revealed_x > revealed_o:
            ai_wants = 'X'
        elif revealed_o > revealed_x:
            ai_wants = 'O'
        else:
            ai_wants = 'X' if self.ai_player_id == 0 else 'O'
        
        # Smart Monty Hall strategy
        if self.difficulty == "expert":
            # Expert: Always use optimal Monty Hall strategy
            # If revealed symbol is what we DON'T want, staying is better (67% vs 33%)
            # If revealed symbol is what we DO want, switching is better
            if monty_symbol != ai_wants:
                return "original"  # Stay with original
            else:
                return "monty"  # Switch to revealed
        
        elif self.difficulty == "hard":
            # Hard: Usually use optimal strategy with some randomness
            if random.random() < 0.85:  # 85% optimal play
                if monty_symbol != ai_wants:
                    return "original"
                else:
                    return "monty"
            else:
                return random.choice(["original", "monty"])
        
        elif self.difficulty == "medium":
            # Medium: Sometimes use optimal strategy
            if random.random() < 0.6:  # 60% optimal play
                if monty_symbol != ai_wants:
                    return "original"
                else:
                    return "monty"
            else:
                return random.choice(["original", "monty"])
        
        else:  # Easy
            # Easy: Mostly random with slight bias toward switching (general Monty Hall advice)
            return random.choice(["original", "original", "monty", "monty", "monty"])  # Slight switch bias