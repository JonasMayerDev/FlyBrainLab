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
  native_trace_verified?: boolean;
  readout_metrics?: { population_mean_rate_hz: number; readout_spike_events: number; readout_active_neurons: number; group_mean_rate_hz?: { left: number; right: number } };
}
export interface Source { title: string; url: string; kind?: string; scope?: string }
export interface RunSummary { run_id: string; file: string; title: string; classification: string; metadata: Metadata; body_available?: boolean }
export interface ReplayIndex {
  schema_version: number; exported_at_utc: string; repository_url: string;
  runs: RunSummary[]; sources: Source[];
  technical_setup_check?: { question: string; interpretation: string; next_decision: string; limitations: string[] };
  comparisons?: { design_id: string; test: string; execution_context: string; run_ids: string[]; url: string; summary: { n_seeds: number; updated_decision: string; inference: string; next_test?: string; sham?: { mean_hz: number }; upstream_drive?: { mean_hz: number; sample_sd_hz: number }; outgoing_disconnected?: { mean_hz: number }; fractional_reduction?: number[] } }[];
  default_run_id?: string;
  discovery?: NativeDiscovery | null;
  coupling?: { comparison_kind: string; interpretation: string; body_execution_context?: string; paired_results: { seed: number; driven_run_id: string; sham_run_id: string; common_horizon_ms: number; root_position_difference_cm_at_common_horizon: number; wing_angle_rms_difference_rad: number; maximum_driven_adapter_command_delta_rad?: number; driven_terminated_early: boolean; sham_terminated_early: boolean }[] };
}
export interface NativeDiscovery {
  verified: boolean; omnigent_version: string; root_conversation_id: string; trace_url: string; trace_sha256: string;
  evidence_mode: string; verification_scope: string; runtime_model: string; runtime_harness: string; unsuccessful_tool_output_count: number;
  stages: { role: string; conversation_id: string; final_item_sha256: string; inbox_result_item_sha256: string; observed_tools: string[]; output_excerpt: string; excerpt_truncated: boolean }[];
  receipts: { receipt_id: string; test: string; wall_seconds: number; url: string; sha256: string; run_ids: string[]; comparison_url: string; design_sha256: string; summary: { next_test: string; n_seeds: number; upstream_drive: { mean_hz: number; sample_sd_hz: number }; sham?: { mean_hz: number }; paired_difference_hz?: number[] } }[];
  analyst_records: { record_id: string; url: string; sha256: string; question: string; candidate_tests: string[]; selected_test: string; updated_decision: string; decision_reason: string; next_test: string; source_ids: string[]; claim_ids: string[]; tool_receipt_ids: string[] }[];
  verified_run_ids: string[];
  followup_traces?: NativeDiscovery[];
  cross_session_followup_proofs?: {
    current_root_conversation_id: string; current_receipt_id: string; followup_test: string;
    prior_root_conversation_id: string; prior_trace_url: string; prior_trace_sha256: string;
    prior_record_id: string; prior_record_url: string; prior_record_sha256: string; prior_next_test: string;
    current_record_read: { call_id: string; content_sha256: string; result_position: number; created_at: number; result_item_sha256: string };
    current_planner_launch_position: number; current_experimenter_launch_position: number;
  }[];
}
export interface BodyState { time_ms: number; position: [number, number, number]; quaternion?: [number, number, number, number]; wing_angles_rad?: number[]; adapter_rate_hz?: number; wing_yaw_amplitude_factor?: number }
export interface BodyReplay {
  run_id?: string; states?: BodyState[]; model?: string; controller?: string; adapter?: { adapter_id?: string } | string; loop?: string;
  position_unit?: string; duration_ms?: number; task_terminated_early?: boolean; limitations?: string[]; run_record_url?: string;
  published_policy?: { source: string; trained_policy: string; new_training_performed: boolean; asset_manifest_sha256: string } | null;
  body_controller_feedback?: boolean; neural_sensor_feedback?: boolean;
  metrics?: { root_displacement_cm?: number; maximum_adapter_rate_hz?: number; maximum_adapter_wingbeat_command_delta_rad?: number; minimum_thorax_height_cm?: number; root_height_change_cm?: number };
}
export interface Replay {
  schema_version: number; run_id: string; title: string; classification: string;
  recorded_simulation: boolean; metadata: Metadata;
  activity: { time_unit: string; event_count: number; events: { time_ms: number; neuron_id: string }[];
    events_complete: boolean; source_complete: boolean; display_sampling: string;
    histogram: { bin_width_ms: number; counts: number[]; complete: boolean } };
  graph: { layout: string; selection: string; nodes: { id: string; target: boolean; readout?: boolean; spike_count: number }[]; edges: unknown[] };
  body?: BodyReplay | null;
  body_variants?: Omit<BodyReplay, 'states' | 'limitations'>[];
  sources: Source[];
  provenance: { run_record_url: string; run_record_sha256: string; spike_source_url: string; spike_source_sha256: string; model_url: string };
}
