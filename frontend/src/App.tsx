import React, { useState } from 'react';
import './App.css';
import Lobby from './components/Lobby';
import Game from './components/Game';

type View = 'lobby' | 'game';

function App(): JSX.Element {
  const [currentView, setCurrentView] = useState<View>('lobby');
  const [roomCode, setRoomCode] = useState<string>('');
  const [playerName, setPlayerName] = useState<string>('');

  const joinRoom = (code: string, name: string): void => {
    setRoomCode(code);
    setPlayerName(name);
    setCurrentView('game');
  };

  const backToLobby = (): void => {
    setCurrentView('lobby');
    setRoomCode('');
    setPlayerName('');
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Entropy TicTacToe</h1>
        <p>Entropy in TicTacToe, crazy ain't it!</p>
      </header>
      
      <main>
        {currentView === 'lobby' ? (
          <Lobby onJoinRoom={joinRoom} />
        ) : (
          <Game 
            roomCode={roomCode} 
            playerName={playerName}
            onBackToLobby={backToLobby}
          />
        )}
      </main>
      
      <footer style={{ 
        position: 'fixed', 
        bottom: '10px', 
        left: '10px', 
        fontSize: '12px', 
        color: '#666',
        zIndex: 1000
      }}>
        made with love from <a 
          href="/blog.html" 
          target="_blank"
          style={{ 
            color: '#007bff', 
            textDecoration: 'none' 
          }}
          onMouseOver={(e) => (e.target as HTMLAnchorElement).style.textDecoration = 'underline'}
          onMouseOut={(e) => (e.target as HTMLAnchorElement).style.textDecoration = 'none'}
        >
          levi
        </a>
      </footer>
    </div>
  );
}

export default App;