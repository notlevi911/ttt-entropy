import React, { useState } from 'react';
import Notification from './Notification';

interface LobbyProps {
  onJoinRoom: (code: string, name: string) => void;
}

interface NotificationType {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
}

const Lobby: React.FC<LobbyProps> = ({ onJoinRoom }) => {
  const [roomCode, setRoomCode] = useState<string>('');
  const [createdRoomCode, setCreatedRoomCode] = useState<string>('');
  const [playerName, setPlayerName] = useState<string>('');
  const [isCreating, setIsCreating] = useState<boolean>(false);
  const [notifications, setNotifications] = useState<NotificationType[]>([]);

  const addNotification = (message: string, type: 'success' | 'error' | 'info' | 'warning' = 'info') => {
    const id = Date.now().toString();
    const newNotification: NotificationType = { id, message, type };
    setNotifications(prev => [...prev, newNotification]);
  };

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const createRoom = async (): Promise<void> => {
    setIsCreating(true);
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/create_room`);
      const data = await response.json();
      setCreatedRoomCode(data.room_code);
    } catch (error) {
      console.error('Error creating room:', error);
      addNotification('Failed to create room. Please try again.', 'error');
    } finally {
      setIsCreating(false);
    }
  };

  const copyRoomCode = (): void => {
    navigator.clipboard.writeText(createdRoomCode);
    addNotification('Room code copied to clipboard!', 'success');
  };

  const joinRoom = (): void => {
    if (roomCode.trim() && playerName.trim()) {
      onJoinRoom(roomCode.toUpperCase(), playerName.trim());
    } else {
      addNotification('Please enter both room code and player name', 'warning');
    }
  };

  const handleRoomCodeChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    setRoomCode(e.target.value.toUpperCase());
  };

  const handlePlayerNameChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    setPlayerName(e.target.value);
  };

  const handleKeyPress = (e: React.KeyboardEvent): void => {
    if (e.key === 'Enter') {
      joinRoom();
    }
  };

  return (
    <div className="lobby">
      <div className="notifications-container">
        {notifications.map(notification => (
          <Notification
            key={notification.id}
            message={notification.message}
            type={notification.type}
            onClose={() => removeNotification(notification.id)}
          />
        ))}
      </div>

      <div className="lobby-container">
        <div className="game-description">
          <h2>Game Rules</h2>
          <ul>
            <li>3×3 board with 9 hidden pieces (5 of one symbol, 4 of another)</li>
            <li>Each piece shows probability percentages, but you don't know which is yours</li>
            <li>Placement Phase: Take turns placing all 9 pieces</li>
            <li>Reveal Phase: Take turns revealing pieces to find 3-in-a-row</li>
            <li>Probabilities update following Monty Hall theorem to determine percentages</li>
            <li>Win by getting 3 of your symbol in a row, column, or diagonal</li>
          </ul>
        </div>

        <div className="lobby-actions">
          <div className="create-room-section">
            <h3>Create New Room</h3>
            <button 
              onClick={createRoom} 
              disabled={isCreating}
              className="create-room-btn"
            >
              {isCreating ? 'Creating...' : 'Create Room'}
            </button>
            
            {createdRoomCode && (
              <div className="created-room">
                <p>Room Code:</p>
                <div className="room-code-display">
                  <span className="room-code-text">{createdRoomCode}</span>
                  <button onClick={copyRoomCode} className="copy-btn">
                    Copy
                  </button>
                </div>
              </div>
            )}
          </div>

          <div className="join-room-section">
            <h3>Join Existing Room</h3>
            <div className="input-group">
              <input
                type="text"
                placeholder="Enter room code (e.g., ABC123)"
                value={roomCode}
                onChange={handleRoomCodeChange}
                onKeyPress={handleKeyPress}
                className="room-code-input"
                maxLength={6}
              />
            </div>
            <div className="input-group">
              <input
                type="text"
                placeholder="Enter your name"
                value={playerName}
                onChange={handlePlayerNameChange}
                onKeyPress={handleKeyPress}
                className="player-name-input"
                maxLength={20}
              />
            </div>
            <button 
              onClick={joinRoom}
              className="join-room-btn"
              disabled={!roomCode.trim() || !playerName.trim()}
            >
              Join Room
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Lobby;