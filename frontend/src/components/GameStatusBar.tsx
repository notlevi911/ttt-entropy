import React from 'react';
import { GameState, RoomInfo, Player } from '../types';

interface GameStatusBarProps {
  gameState: GameState;
  roomInfo: RoomInfo | null;
  currentPlayer?: Player;
  isMyTurn: boolean;
}

const GameStatusBar: React.FC<GameStatusBarProps> = ({
  gameState,
  roomInfo,
  currentPlayer,
  isMyTurn
}) => {
  const getCurrentTurnPlayer = (): Player | null => {
    if (!roomInfo) return null;
    return roomInfo.players.find(p => p.id === gameState.current_turn) || null;
  };

  const getPhaseDisplay = (): string => {
    switch (gameState.phase) {
      case 'placement':
        return 'Placement Phase';
      case 'reveal':
        return 'Reveal Phase';
      default:
        return 'Unknown Phase';
    }
  };

  const getGameStatus = (): JSX.Element => {
    if (gameState.game_over) {
      if (gameState.winner) {
        const isWinner = gameState.winner === (gameState.player_id === 0 ? 'X' : 'O');
        return (
          <div className={`game-status ${isWinner ? 'winner' : 'loser'}`}>
            <strong>{gameState.winner} Wins!</strong>
            {isWinner ? ' You won!' : ' Better luck next time!'}
          </div>
        );
      } else {
        return (
          <div className="game-status draw">
            <strong>It's a Draw!</strong> Good game!
          </div>
        );
      }
    }

    const currentTurnPlayer = getCurrentTurnPlayer();
    const turnText = isMyTurn ? 'Your Turn' : `${currentTurnPlayer?.name || 'Opponent'}'s Turn`;
    
    return (
      <div className={`game-status ${isMyTurn ? 'my-turn' : 'opponent-turn'}`}>
        <strong>{turnText}</strong>
        {isMyTurn ? ' - Make your move!' : ' - Please wait...'}
      </div>
    );
  };

  const getPlayerSymbol = (playerId: number): string => {
    // Player 0 is X, Player 1 is O (this is just for display, actual symbols are hidden)
    return playerId === 0 ? 'X' : 'O';
  };

  return (
    <div className="game-status-bar">
      <div className="status-section">
        <div className="phase-info">
          {getPhaseDisplay()}
        </div>
        {getGameStatus()}
        
        {!gameState.game_over && gameState.turn_time_remaining !== undefined && gameState.turn_time_remaining !== null && (
          <div className={`turn-timer ${(gameState.turn_time_remaining || 0) <= 10 ? 'urgent' : ''}`}>
            Time: {gameState.turn_time_remaining || 0}s
          </div>
        )}
      </div>

      <div className="players-section">
        <h4>Players ({roomInfo?.players.length || 0}/2)</h4>
        <div className="players-list">
          {roomInfo?.players.map(player => (
            <div 
              key={player.id} 
              className={`player-info ${player.id === currentPlayer?.id ? 'current-player' : ''}`}
            >
              <span className="player-symbol">
                {getPlayerSymbol(player.id)}
              </span>
              <span className="player-name">
                {player.name}
                {player.id === currentPlayer?.id && ' (You)'}
              </span>
              {gameState.current_turn === player.id && !gameState.game_over && (
                <span className="turn-indicator">•</span>
              )}
            </div>
          )) || []}
        </div>

        {roomInfo?.waiting_for_player && (
          <div className="waiting-for-player">
            Waiting for another player to join...
          </div>
        )}
      </div>

      <div className="game-info">
        <div className="info-item">
          <span className="info-label">Room:</span>
          <span className="info-value">{roomInfo?.code}</span>
        </div>
        <div className="info-item">
          <span className="info-label">Phase:</span>
          <span className="info-value">{gameState.phase}</span>
        </div>
        {gameState.phase === 'placement' && (
          <div className="info-item">
            <span className="info-label">Pieces Placed:</span>
            <span className="info-value">
              {gameState.board.filter(cell => cell !== null).length}/9
            </span>
          </div>
        )}
        {gameState.phase === 'reveal' && (
          <div className="info-item">
            <span className="info-label">Pieces Revealed:</span>
            <span className="info-value">
              {gameState.revealed_cells.filter(Boolean).length}/9
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default GameStatusBar;