export interface Metadata {
  run_id: string; status: string; started_at_utc: string; dataset_version: string;
  model_commit: string; duration_ms: number; stimulus_rate_hz: number; seed: number;
  timestep_ms: number; n_trials: number; neurons: number; connection_rows: number;
  spike_events: number; active_neurons: number; full_network_included: boolean;
  wall_seconds: number; body_connected: boolean; evidence_scope: string;
  limitations?: string[]; versions?: Record<string, string>;
  compatibility_adjustments?: string[]; data_loading_adjustments?: string[];
  stimulated_neuron_ids: string[]; readout_neuron_ids?: string[];
  experiment_id?: string; condition?: string; hypothesis?: string; question?: string;
  backend?: string; orchestration?: unknown; metrics?: Record<string, unknown>;
  design_id?: string; execution_context?: string; orchestration_verified_by_this_module?: boolean;
  readout_metrics?: { population_mean_rate_hz: number; readout_spike_events: number; readout_active_neurons: number; group_mean_rate_hz?: { left: number; right: number } };
}
export interface Source { title: string; url: string; kind?: string; scope?: string }
export interface RunSummary { run_id: string; file: string; title: string; classification: string; metadata: Metadata; body_available?: boolean }
export interface ReplayIndex {
  schema_version: number; exported_at_utc: string; repository_url: string;
  runs: RunSummary[]; sources: Source[];
  technical_setup_check?: { question: string; interpretation: string; next_decision: string; limitations: string[] };
  comparisons?: { design_id: string; test: string; execution_context: string; run_ids: string[]; url: string; summary: { n_seeds: number; updated_decision: string; inference: string; next_test?: string; sham?: { mean_hz: number }; upstream_drive?: { mean_hz: number; sample_sd_hz: number }; outgoing_disconnected?: { mean_hz: number }; fractional_reduction?: number[] } }[];
}
export interface BodyState { time_ms: number; position: [number, number, number]; quaternion?: [number, number, number, number]; wing_angles_rad?: number[]; adapter_rate_hz?: number; wing_yaw_amplitude_factor?: number }
export interface Replay {
  schema_version: number; run_id: string; title: string; classification: string;
  recorded_simulation: boolean; metadata: Metadata;
  activity: { time_unit: string; event_count: number; events: { time_ms: number; neuron_id: string }[];
    events_complete: boolean; source_complete: boolean; display_sampling: string;
    histogram: { bin_width_ms: number; counts: number[]; complete: boolean } };
  graph: { layout: string; selection: string; nodes: { id: string; target: boolean; readout?: boolean; spike_count: number }[]; edges: unknown[] };
  body?: { states?: BodyState[]; model?: string; controller?: string; adapter?: { adapter_id?: string } | string; loop?: string; position_unit?: string; duration_ms?: number; task_terminated_early?: boolean; limitations?: string[]; run_record_url?: string; metrics?: { root_displacement_cm?: number; maximum_adapter_rate_hz?: number } } | null;
  sources: Source[];
  provenance: { run_record_url: string; run_record_sha256: string; spike_source_url: string; spike_source_sha256: string; model_url: string };
}
