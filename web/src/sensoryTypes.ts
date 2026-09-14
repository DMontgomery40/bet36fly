export type Metric = { n: number; accuracy: number; log_loss: number; brier: number };
export type Method = 'neural' | 'encoder_only' | 'same_information' | 'uniform' | 'prior' | 'circuit_silenced';
export type Cell = { body_id: number; type: string; native_alias: string };
export type Summary = { status: 'available'; identity: string; correct: number; candidate: string; teams: string[]; evaluation: {
  metrics: Record<Method, Metric>; accuracy_interval: [number, number]; paired_loss: Record<Exclude<Method, 'neural'>, { mean: number; interval: [number, number] }>;
  weeks: number; replicates: number; start: string; end: string; exclusions: Record<string, number>;
}; splits: Record<'training' | 'development' | 'confirmation', { years: string; n: number }>;
source: { source_url: string; source_fetched_at: string; created_at: string }; output_cells: Cell[];
downloads: { id: string; label: string; url: string; sha256: string }[] };
export type SummaryState = Summary | { status: 'unavailable' | 'invalid'; identity: string; message: string };
export type ConfirmationGame = { game_id: string; start_time: string; home: string; away: string; home_win: number; neural: number; encoder_only: number; same_information: number; correct: boolean };
export type GamesPage = { identity: string; games: ConfirmationGame[]; total: number; offset: number; limit: number; summary: { n: number; correct: number; accuracy: number | null; log_loss: number | null } };
export type Probe = { team: string; quality: number; interval: [number, number]; condition: string; contact_key: number; recruited_ids: number[]; requested_hz: number; outputs_hz: number[]; seeds: number[]; outputs_by_seed: number[][]; source_measurement: { tastant: string; mM: number; mean_hz: number; sem_hz: number; sensillum: string } };
export type GameDetail = { identity: string; game: ConfirmationGame; home: Probe; away: Probe; output_cells: Cell[]; stimulus_window_ms: [number, number]; duration_ms: number; trace_note: string; achieved_input_note: string };
