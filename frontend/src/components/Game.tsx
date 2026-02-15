import React, { useState, useEffect, useRef } from 'react';
import { GameState, WebSocketMessage, Player, RoomInfo } from '../types';
import GameBoard from './GameBoard';
import ChatPanel from './ChatPanel';
import GameStatusBar from './GameStatusBar';
import Notification from './Notification';

interface GameProps {
  roomCode: string;
  playerName: string;
  onBackToLobby: () => void;
}

interface Notification {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
}

const Game: React.FC<GameProps> = ({ roomCode, playerName, onBackToLobby }) => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [roomInfo, setRoomInfo] = useState<RoomInfo | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('connecting');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [chatMessages, setChatMessages] = useState<WebSocketMessage[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [playAgainStatus, setPlayAgainStatus] = useState<string>('');
  
  const wsRef = useRef<WebSocket | null>(null);

  const addNotification = (message: string, type: 'success' | 'error' | 'info' | 'warning' = 'info') => {
    const id = Date.now().toString();
    const newNotification: Notification = { id, message, type };
    setNotifications(prev => [...prev, newNotification]);
  };

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  useEffect(() => {
    connectToRoom();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [roomCode]);

  const connectToRoom = (): void => {
    const wsUrl = `ws://localhost:8000/ws/${roomCode}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('Connected to room:', roomCode);
      setConnectionStatus('connected');
      setErrorMessage('');
      
      // Send join message with player name
      ws.send(JSON.stringify({
        type: 'join',
        player_name: playerName
      }));
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        handleWebSocketMessage(message);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket connection closed');
      setConnectionStatus('disconnected');
    };

    ws.onerror = () => {
      console.error('WebSocket connection error');
      setConnectionStatus('error');
      setErrorMessage('Failed to connect to game server');
    };
  };

  const handleWebSocketMessage = (message: WebSocketMessage): void => {
    switch (message.type) {
      case 'game_state':
        if (message.data) {
          setGameState(message.data);
        }
        if (message.room_info) {
          setRoomInfo(message.room_info);
        }
        break;

      case 'player_joined':
        if (message.room_info) {
          setRoomInfo(message.room_info);
        }
        break;

      case 'player_left':
        if (message.player_id !== undefined && roomInfo) {
          const updatedRoomInfo = {
            ...roomInfo,
            players: roomInfo.players.filter(p => p.id !== message.player_id)
          };
          setRoomInfo(updatedRoomInfo);
        }
        break;

      case 'room_closed':
        addNotification(message.message || 'The room has been closed.', 'error');
        setTimeout(() => onBackToLobby(), 2000);
        break;

      case 'play_again_vote':
        if (message.message) {
          setPlayAgainStatus(message.message);
        }
        break;

      case 'game_reset':
        setPlayAgainStatus('');
        addNotification('New game started!', 'success');
        break;

      case 'chat_message':
        setChatMessages(prev => [...prev, message]);
        break;

      case 'error':
        setErrorMessage(message.message || 'An error occurred');
        setConnectionStatus('error');
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  };

  const sendMessage = (message: any): void => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  };

  const placePiece = (position: number): void => {
    sendMessage({
      type: 'place_piece',
      position
    });
  };

  const revealPiece = (position: number): void => {
    sendMessage({
      type: 'reveal_piece',
      position
    });
  };

  const sendChatMessage = (message: string): void => {
    sendMessage({
      type: 'chat_message',
      message
    });
  };

  const playAgain = (): void => {
    sendMessage({
      type: 'play_again'
    });
  };

  if (connectionStatus === 'connecting') {
    return (
      <div className="game-loading">
        <h2>Connecting to room {roomCode}...</h2>
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (connectionStatus === 'error' || !gameState) {
    return (
      <div className="game-error">
        <h2>Connection Error</h2>
        <p>{errorMessage}</p>
        <button onClick={onBackToLobby} className="back-btn">
          Back to Lobby
        </button>
      </div>
    );
  }

  const currentPlayer = roomInfo?.players.find(p => p.id === gameState.player_id);
  const isMyTurn = gameState.current_turn === gameState.player_id;

  return (
    <div className="game">
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

      <div className="game-header">
        <div className="room-info">
          <h2>Room: {roomCode}</h2>
          <button onClick={onBackToLobby} className="back-btn">
            Back to Lobby
          </button>
        </div>
        
        <GameStatusBar 
          gameState={gameState}
          roomInfo={roomInfo}
          currentPlayer={currentPlayer}
          isMyTurn={isMyTurn}
        />
      </div>

      {playAgainStatus && (
        <div className="play-again-status waiting">
          {playAgainStatus}
        </div>
      )}

      <div className="game-content">
        <div className="game-board-container">
          <GameBoard
            gameState={gameState}
            roomInfo={roomInfo}
            onPlacePiece={placePiece}
            onRevealPiece={revealPiece}
            onPlayAgain={playAgain}
            onBackToLobby={onBackToLobby}
            isMyTurn={isMyTurn}
          />
        </div>

        <div className="chat-container">
          <ChatPanel
            messages={chatMessages}
            onSendMessage={sendChatMessage}
            currentPlayer={currentPlayer}
          />
        </div>
      </div>
    </div>
  );
};

export default Game;