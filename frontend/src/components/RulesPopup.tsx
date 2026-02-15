import React from 'react';

interface RulesPopupProps {
  isOpen: boolean;
  onClose: () => void;
}

const RulesPopup: React.FC<RulesPopupProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="rules-overlay" onClick={onClose}>
      <div className="rules-popup" onClick={e => e.stopPropagation()}>
        <div className="rules-header">
          <h3>GAME RULES</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <div className="rules-content">
          <div className="rule-section">
            <h4>BASIC RULES</h4>
            <ul>
              <li>3×3 grid with 9 total pieces</li>
              <li>Exactly 5 of one symbol, 4 of the other</li>
              <li>Each piece shows two probability percentages</li>
              <li><strong>Players don't know which % is for which symbol (X/O)</strong></li>
              <li>Win by getting 3 symbols in a row, column, or diagonal</li>
            </ul>
          </div>

          <div className="rule-section">
            <h4>PLACEMENT PHASE</h4>
            <ul>
              <li>Players alternate placing pieces on empty cells</li>
              <li>All symbols remain hidden during placement</li>
              <li>Center piece is auto-placed</li>
              <li>After all pieces placed → reveal phase begins</li>
            </ul>
          </div>

          <div className="rule-section">
            <h4>REVEAL PHASE</h4>
            <ul>
              <li>Players take turns revealing pieces</li>
              <li>Revealed symbols help identify which % is X/O</li>
              <li>Probabilities update after each reveal</li>
              <li>First to get 3 in a row wins</li>
              <li>If all revealed with no winner → draw</li>
            </ul>
          </div>

          <div className="rule-section">
            <h4>TURN TIMER</h4>
            <p>Each player has 30 seconds per turn. If time runs out, turn automatically passes to opponent.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RulesPopup;