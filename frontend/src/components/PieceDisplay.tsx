import React from 'react';
import { GameState } from '../types';

interface PieceDisplayProps {
  position: number;
  gameState: GameState;
}

const PieceDisplay: React.FC<PieceDisplayProps> = ({ position, gameState }) => {
  const { board, probabilities, revealed_cells, phase } = gameState;

  // If cell is empty
  if (board[position] === null) {
    return <div className="piece-empty">+</div>;
  }

  // If piece is revealed, show the actual symbol
  if (revealed_cells[position]) {
    const symbol = board[position];
    return (
      <div className={`piece-revealed piece-${symbol?.toLowerCase()}`}>
        {symbol}
      </div>
    );
  }

  // If piece is placed but not revealed, show probabilities
  if (board[position] === 'placed') {
    const [prob1, prob2] = probabilities[position];
    
    // Handle center piece during placement phase (hidden probabilities)
    if (phase === 'placement' && position === 4 && (prob1 === null || prob2 === null)) {
      return (
        <div className="piece-probability center-hidden">
          <div className="prob-line">? %</div>
          <div className="prob-divider">/</div>
          <div className="prob-line">? %</div>
        </div>
      );
    }

    return (
      <div className="piece-probability">
        <div className="prob-line">{prob1}%</div>
        <div className="prob-divider">/</div>
        <div className="prob-line">{prob2}%</div>
      </div>
    );
  }

  // Fallback for unexpected states
  return <div className="piece-empty">?</div>;
};

export default PieceDisplay;