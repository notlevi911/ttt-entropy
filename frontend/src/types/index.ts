export interface GameState {
  board: (string | null)[];
  probabilities: (readonly [number, number] | readonly [null, null])[];
  phase: 'placement' | 'reveal';
  current_turn: number;
  revealed_cells: boolean[];
  winner: string | null;
  game_over: boolean;
  player_id: number;
  play_again_votes?: boolean[];
}

export interface Player {
  id: number;
  name: string;
}

export interface RoomInfo {
  code: string;
  players: Player[];
  waiting_for_player?: boolean;
}

export interface WebSocketMessage {
  type: string;
  data?: any;
  room_info?: RoomInfo;
  player?: Player;
  player_id?: number;
  player_name?: string;
  message?: string;
  timestamp?: string;
}