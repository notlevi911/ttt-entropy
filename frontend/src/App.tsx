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
        <p>A multiplayer hidden-information strategy game</p>
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
    </div>
  );
}

export default App;