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
  turn_time_remaining?: number;
  turn_timeout?: number;
  monty_hall_state?: {
    player_id: number;
    original_position: number;
    monty_position: number;
    monty_symbol: string;
  } | null;
}

export interface Player {
  id: number;
  name: string;
  is_ai?: boolean;
}

export interface RoomInfo {
  code: string;
  players: Player[];
  waiting_for_player?: boolean;
  ai_mode?: boolean;
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
  // Monty Hall specific properties
  original_position?: number;
  revealed_position?: number;
  revealed_symbol?: string;
  monty_symbol?: string;
  monty_position?: number;
  piece_type?: string;
  strategy_hint?: string;
  private_reveal?: boolean;
  public_reveal?: boolean;
  position?: number;
  symbol?: string;
}