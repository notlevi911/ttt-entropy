import React, { useState, useRef, useEffect } from 'react';
import { WebSocketMessage, Player } from '../types';

interface ChatPanelProps {
  messages: WebSocketMessage[];
  onSendMessage: (message: string) => void;
  currentPlayer?: Player;
}

const ChatPanel: React.FC<ChatPanelProps> = ({ messages, onSendMessage, currentPlayer }) => {
  const [inputMessage, setInputMessage] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = (): void => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = (): void => {
    const message = inputMessage.trim();
    if (message) {
      onSendMessage(message);
      setInputMessage('');
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>): void => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    setInputMessage(e.target.value);
  };

  const formatTimestamp = (timestamp?: string): string => {
    if (!timestamp) return '';
    
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  const getMessageClass = (message: WebSocketMessage): string => {
    const isOwnMessage = message.player_id === currentPlayer?.id;
    return `chat-message ${isOwnMessage ? 'own-message' : 'other-message'}`;
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <h3>💬 Chat</h3>
      </div>

      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="no-messages">
            <p>No messages yet. Say hello! 👋</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div key={index} className={getMessageClass(message)}>
              <div className="message-header">
                <span className="player-name">
                  {message.player_name || 'Unknown Player'}
                </span>
                <span className="message-time">
                  {formatTimestamp(message.timestamp)}
                </span>
              </div>
              <div className="message-content">
                {message.message}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input">
        <input
          ref={inputRef}
          type="text"
          placeholder="Type a message..."
          value={inputMessage}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          maxLength={200}
          className="message-input"
        />
        <button
          onClick={handleSendMessage}
          disabled={!inputMessage.trim()}
          className="send-button"
        >
          📤
        </button>
      </div>
    </div>
  );
};

export default ChatPanel;