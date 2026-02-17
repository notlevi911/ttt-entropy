import React from 'react';
import { GameState, RoomInfo } from '../types';
import PieceDisplay from './PieceDisplay';

interface GameBoardProps {
  gameState: GameState;
  roomInfo: RoomInfo | null;
  onPlacePiece: (position: number) => void;
  onRevealPiece: (position: number) => void;
  onPlayAgain: () => void;
  onBackToLobby: () => void;
  isMyTurn: boolean;
}

const GameBoard: React.FC<GameBoardProps> = ({
  gameState,
  roomInfo,
  onPlacePiece,
  onRevealPiece,
  onPlayAgain,
  onBackToLobby,
  isMyTurn
}) => {
  const canInteract = (): boolean => {
    if (!roomInfo || roomInfo.waiting_for_player) {
      return false;
    }
    
    // Check if it's AI's turn
    if (roomInfo.ai_mode) {
      const currentTurnPlayer = roomInfo.players.find(p => p.id === gameState.current_turn);
      if (currentTurnPlayer?.is_ai) {
        return false; // Can't interact when it's AI's turn
      }
    }
    
    return isMyTurn && !gameState.game_over;
  };

  const handleCellClick = (position: number): void => {
    if (!canInteract()) return;

    if (gameState.phase === 'placement') {
      // During placement phase, can only place on empty cells (except center)
      if (gameState.board[position] === null && position !== 4) {
        onPlacePiece(position);
      }
    } else if (gameState.phase === 'reveal') {
      // During reveal phase, can only reveal placed but unrevealed pieces
      if (gameState.board[position] === 'placed' && !gameState.revealed_cells[position]) {
        onRevealPiece(position);
      }
    }
  };

  const getCellClass = (position: number): string => {
    const baseClass = 'game-cell';
    const classes = [baseClass];

    if (gameState.board[position] === null) {
      classes.push('empty');
    } else if (gameState.board[position] === 'placed') {
      classes.push('placed');
    } else if (gameState.revealed_cells[position]) {
      classes.push('revealed');
      classes.push(`revealed-${gameState.board[position]?.toLowerCase()}`);
    }

    // Handle Monty Hall state visual indicators
    if (gameState.monty_hall_state && isMyTurn) {
      if (position === gameState.monty_hall_state.original_position) {
        classes.push('monty-original');
        classes.push('clickable');
      } else if (position === gameState.monty_hall_state.monty_position) {
        classes.push('monty-choice');
        classes.push('clickable');
      }
    } else {
      // Normal game logic when not in Monty Hall state
      if (isMyTurn) {
        if (gameState.phase === 'placement' && gameState.board[position] === null) {
          classes.push('clickable');
        } else if (
          gameState.phase === 'reveal' && 
          gameState.board[position] === 'placed' && 
          !gameState.revealed_cells[position]
        ) {
          classes.push('clickable');
        }
      }
    }

    // Add winner highlight if this cell is part of winning line
    if (gameState.winner && gameState.revealed_cells[position]) {
      const winPatterns = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], // rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8], // columns
        [0, 4, 8], [2, 4, 6] // diagonals
      ];

      for (const pattern of winPatterns) {
        if (pattern.includes(position)) {
          const symbols = pattern.map(i => gameState.board[i]);
          if (symbols.every(s => s === gameState.winner && gameState.revealed_cells[pattern[0]] && gameState.revealed_cells[pattern[1]] && gameState.revealed_cells[pattern[2]])) {
            classes.push('winning-cell');
            break;
          }
        }
      }
    }

    return classes.join(' ');
  };

  return (
    <div className="game-board">
      {roomInfo?.waiting_for_player && (
        <div className="waiting-overlay">
          <div className="waiting-message">
            <h3>WAITING FOR PLAYER</h3>
            <p>Room needs 2 players to start</p>
            <div className="loading-spinner"></div>
          </div>
        </div>
      )}
      
      <div className="board-grid">
        {Array.from({ length: 9 }, (_, index) => (
          <div
            key={index}
            className={getCellClass(index)}
            onClick={() => handleCellClick(index)}
          >
            <PieceDisplay
              position={index}
              gameState={gameState}
            />
          </div>
        ))}
      </div>

      <div className="game-instructions">
        {gameState.monty_hall_state && isMyTurn && (
          <div className="monty-hall-instructions">
            <p><strong>MONTY HALL TRIGGERED!</strong></p>
            <p>Green box contains: <strong>{gameState.monty_hall_state.monty_symbol}</strong></p>
          </div>
        )}
        {!gameState.monty_hall_state && gameState.phase === 'placement' && !gameState.game_over && (
          <p>
            <strong>Placement Phase:</strong> Click empty cells to place pieces
            {!isMyTurn && ' (waiting for other player)'}
          </p>
        )}
        {!gameState.monty_hall_state && gameState.phase === 'reveal' && !gameState.game_over && (
          <p>
            <strong>Reveal Phase:</strong> Click pieces to reveal their symbols
            {!isMyTurn && ' (waiting for other player)'}
          </p>
        )}
        {gameState.game_over && (
          <div className="game-end">
            {gameState.winner ? (
              <p className="winner-message">
                <strong>Game Over:</strong> {gameState.winner} wins!
              </p>
            ) : (
              <p className="draw-message">
                <strong>Game Over:</strong> It's a draw!
              </p>
            )}
            
            <div className="game-end-actions">
              <button onClick={onPlayAgain} className="play-again-btn">
                Play Again
              </button>
              <button onClick={onBackToLobby} className="exit-room-btn">
                Exit Room
              </button>
            </div>
            
            {gameState.play_again_votes && !roomInfo?.ai_mode && (
              <div className="play-again-status">
                {gameState.play_again_votes.some((vote: boolean) => vote) && (
                  <p>Waiting for all players to vote for play again...</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default GameBoard;