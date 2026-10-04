import './style.css';
import { NeuralScene } from './scene';
import type { Metadata, Replay, ReplayIndex, RunSummary, Source } from './types';

const app = document.querySelector<HTMLDivElement>('#app')!;
const REPO = 'https://github.com/JonasMayerDev/FlyBrainLab';
const icon = {
  arrow: '<svg viewBox="0 0 24 24"><path d="M7 17 17 7M7 7h10v10"/></svg>',
  play: '<svg viewBox="0 0 24 24"><path d="m9 5 11 7-11 7Z"/></svg>',
  pause: '<svg viewBox="0 0 24 24"><path d="M8 5v14M16 5v14"/></svg>',
  reset: '<svg viewBox="0 0 24 24"><path d="M4 11a8 8 0 1 1 2 7M4 4v7h7"/></svg>',
  fly: '<svg viewBox="0 0 36 36"><path d="M18 10v22M13 26l5-6 5 6"/><ellipse cx="12" cy="12" rx="6" ry="10" transform="rotate(-35 12 12)"/><ellipse cx="24" cy="12" rx="6" ry="10" transform="rotate(35 24 12)"/></svg>',
  circle: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/></svg>',
  layers: '<svg viewBox="0 0 24 24"><path d="m12 3 10 6-10 6L2 9Zm-9 11 9 5 9-5M3 18l9 5 9-5"/></svg>',
  chevron: '<svg viewBox="0 0 24 24"><path d="m9 5 7 7-7 7"/></svg>',
};
const h = (value: unknown) => String(value ?? '').replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]!));
const link = (url: string) => /^https:\/\//.test(url) ? h(url) : '#';
const format = (value: number | undefined) => typeof value === 'number' ? value.toLocaleString('en-US', { maximumFractionDigits: 3 }) : '—';
const short = (id: string) => `${id.slice(0, 6)}…${id.slice(-6)}`;
const science = (item: Replay | RunSummary) => item.classification !== 'technical_setup_check';
let index: ReplayIndex;
let run: Replay;
let scene: NeuralScene | undefined;
let currentTime = 0;
let playing = false;
let lastFrame = 0;
let playbackSeconds = 10;
let activeMode: 'neural' | 'body' = 'neural';
let activeTab: 'results' | 'parameters' | 'evidence' | 'method' | 'trace' = 'results';
let loadingToken = 0;
const cache = new Map<string, Replay>();
const nativeTest = (id: string) => index.discovery?.receipts.find(receipt => receipt.run_ids.includes(id))?.test;

function frameShell(): void {
  app.innerHTML = `
    <header class="topbar"><a class="brand" href="./">${icon.fly}<span>FlyBrain<span class="brand-light">Lab</span><small>AGENTIC SCIENTIFIC DISCOVERY</small></span></a>
      <nav aria-label="Project links"><span class="challenge"><span class="status-dot"></span>Challenge 03 · Databricks</span><a class="repo-link" href="./lab/board.html">Expert board &amp; results ${icon.arrow}</a><a class="repo-link" href="${REPO}" target="_blank" rel="noopener">Repository ${icon.arrow}</a></nav></header>
    <div class="layout"><aside class="sidebar"><div class="sidebar-heading"><span class="eyebrow">EXPERIMENT LIBRARY</span><span id="run-count" class="small-pill">—</span></div>
      <p class="sidebar-intro">Recorded runs. Inspect the stimulus, response and controls.</p><div id="run-list" aria-label="Recorded experiments"><div class="loading">Loading recorded experiments…</div></div>
      <div class="sidebar-footer"><span class="eyebrow">MODEL SNAPSHOT</span><p>FAFB / FlyWire <strong>v783</strong></p><div class="mini-stat"><span>Neurons in the model</span><b>138,639</b></div><div class="mini-stat"><span>Connection rows</span><b>15,091,983</b></div><a href="${REPO}/blob/main/data/brain/manifest.json" target="_blank" rel="noopener">Dataset manifest ${icon.arrow}</a></div></aside>
    <main><div class="intro"><div><div class="eyebrow intro-label"><span class="status-dot"></span>EXPLORE A REAL RECORDED SIMULATION</div><h1>A connectome.<br>A question. <em>An experiment.</em></h1><p>Trace neural stimulation through a whole-network model.<br>Check the evidence. Compare the controls. See what we can claim.</p></div><div class="recording-badge">${icon.circle}<span>RECORDED REPLAY<small>Computed locally · no live simulation</small></span></div></div>
      <section class="workspace" aria-label="Simulation replay"><div class="visual"><div class="visual-top"><div><span class="eyebrow">ACTIVITY EXPLORER</span><h2 id="run-title">Loading…</h2></div><div class="view-switch" aria-label="Visualization mode"><button id="neural-mode" class="active" aria-pressed="true">Neural activity</button><button id="body-mode" aria-pressed="false" disabled>Body trajectory</button></div></div>
        <div id="scene" class="scene"><div id="scene-error" hidden></div></div><div class="scene-overlay"><span id="scene-label" class="scene-caption">Abstract layout · real neuron IDs</span><button id="body-camera" class="body-camera" aria-pressed="true" title="Follow the recorded fly; turn off to frame the full trajectory" hidden>Follow fly</button><span class="view-hint">Drag to orbit · scroll to zoom</span><button id="reset-view" class="icon-button" aria-label="Reset camera">${icon.reset}</button></div>
        <div class="legend"><span><i class="lime"></i>Stimulated target</span><span><i class="white"></i>Recorded spike</span><span><i class="muted"></i>Sampled model cell</span><span id="sample-count"></span></div>
        <div class="transport"><button id="play" class="play-button" aria-label="Play recorded simulation">${icon.play}</button><div class="timeline-group"><div class="timeline-labels"><span id="time-value">0.0 ms</span><span id="duration-value">— ms</span></div><input id="timeline" type="range" min="0" max="20" value="0" step="0.1" aria-label="Simulation time in milliseconds" /></div><label class="speed-label">Replay length<select id="replay-speed" aria-label="Playback duration"><option value="10">10 seconds</option><option value="20">20 seconds</option><option value="5">5 seconds</option></select></label></div>
        <div class="chart-heading"><span>RECORDED SPIKE EVENTS / TIME BIN</span><span id="chart-range"></span></div><canvas id="activity-chart" aria-label="Recorded neural activity histogram" role="img"></canvas>
      </div><aside class="run-panel"><div id="run-context"></div><div class="metric-row"><div><span>Spike events</span><strong id="spike-count">—</strong></div><div><span>Active cells</span><strong id="active-count">—</strong></div></div><div id="run-insight"></div><div class="node-inspector"><div class="eyebrow">INSPECT A NEURON</div><label for="neuron-select" class="sr-only">Select a model neuron</label><select id="neuron-select"></select><div id="neuron-detail"></div></div><a id="raw-link" class="text-link" target="_blank" rel="noopener">Open original run record ${icon.arrow}</a></aside></section>
      <section class="details" aria-label="Experiment evidence and parameters"><div class="tabs" role="tablist"><button id="tab-results" role="tab" aria-controls="tab-content" aria-selected="true" tabindex="0">Control comparison</button><button id="tab-trace" role="tab" aria-controls="tab-content" aria-selected="false" tabindex="-1">Omnigent trace</button><button id="tab-parameters" role="tab" aria-controls="tab-content" aria-selected="false" tabindex="-1">Parameters</button><button id="tab-evidence" role="tab" aria-controls="tab-content" aria-selected="false" tabindex="-1">Evidence & sources</button><button id="tab-method" role="tab" aria-controls="tab-content" aria-selected="false" tabindex="-1">Scope & method</button></div><div id="tab-content" role="tabpanel" aria-labelledby="tab-results"></div></section>
      <section class="research-path"><div><span class="eyebrow">FROM QUESTION TO NEXT DECISION</span><h2>Make the discovery traceable.</h2><p>Omnigent coordinates the research process; Brian2 computes neural dynamics. A replay lets you inspect the resulting records.</p></div><ol><li><span>01</span>Evidence</li><li><span>02</span>Hypothesis</li><li><span>03</span>Controlled test</li><li><span>04</span>Result</li><li><span>05</span>Next decision</li></ol><a href="${REPO}/blob/main/TEAM_STATUS.md" target="_blank" rel="noopener">Read the verified project status ${icon.arrow}</a></section>
      <footer><span>FlyBrainLab · Global AI Hackathon 2026, Munich</span><span>Observed model behavior ≠ validated biological function.</span></footer>
    </main></div><div id="live-status" class="sr-only" role="status" aria-live="polite"></div>`;
  try { scene = new NeuralScene(document.querySelector('#scene')!, selectNeuron, updateTime); }
  catch { const error = document.querySelector<HTMLDivElement>('#scene-error')!; error.hidden = false; error.innerHTML = '<strong>3D rendering is unavailable in this browser.</strong><p>All recorded results, controls, neuron IDs and the time histogram remain available below.</p>'; }
  document.querySelector('#play')!.addEventListener('click', () => { if (run && currentTime >= run.metadata.duration_ms) currentTime = 0; setPlaying(!playing); });
  document.querySelector<HTMLInputElement>('#timeline')!.addEventListener('input', event => { currentTime = Number((event.target as HTMLInputElement).value); setPlaying(false); updateTime(); });
  document.querySelector<HTMLSelectElement>('#replay-speed')!.addEventListener('change', event => { playbackSeconds = Number((event.target as HTMLSelectElement).value); });
  document.querySelector('#reset-view')!.addEventListener('click', () => scene?.reset());
  document.querySelector('#body-camera')!.addEventListener('click', () => { scene?.toggleBodyCamera(); updateTime(); });
  document.querySelector<HTMLSelectElement>('#neuron-select')!.addEventListener('change', event => selectNeuron((event.target as HTMLSelectElement).value));
  for (const mode of ['neural', 'body'] as const) document.querySelector(`#${mode}-mode`)!.addEventListener('click', () => {
    activeMode = mode;
    scene?.setMode(mode);
    for (const value of ['neural', 'body']) { const button = document.querySelector(`#${value}-mode`)!; button.classList.toggle('active', value === mode); button.setAttribute('aria-pressed', String(value === mode)); }
    updateTime();
  });
  const tabs = ['results', 'trace', 'parameters', 'evidence', 'method'] as const;
  tabs.forEach((tab, tabIndex) => {
    const button = document.querySelector<HTMLButtonElement>(`#tab-${tab}`)!;
    button.addEventListener('click', () => selectTab(tab));
    button.addEventListener('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      const destination = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (tabIndex + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
      selectTab(tabs[destination]); document.querySelector<HTMLButtonElement>(`#tab-${tabs[destination]}`)!.focus();
    });
  });
}

async function get<T>(file: string): Promise<T> {
  const response = await fetch(`${import.meta.env.BASE_URL}replays/${file}`);
  if (!response.ok) throw new Error(`Replay file unavailable (HTTP ${response.status}).`);
  return response.json();
}

function library(): void {
  const groups = [{ name: 'VERIFIED OMNIGENT RUNS', items: index.runs.filter(item => item.metadata.native_trace_verified) }, { name: 'OTHER RECORDED MODEL RUNS', items: index.runs.filter(item => science(item) && !item.metadata.native_trace_verified && item.metadata.execution_context !== 'independent-feasibility-before-Omnigent') }, { name: 'INDEPENDENT FEASIBILITY RUNS', items: index.runs.filter(item => science(item) && item.metadata.execution_context === 'independent-feasibility-before-Omnigent') }, { name: 'TECHNICAL SETUP CHECKS', items: index.runs.filter(item => !science(item)) }];
  document.querySelector('#run-count')!.textContent = String(index.runs.length);
  document.querySelector('#run-list')!.innerHTML = groups.filter(group => group.items.length).map(group => `<div class="run-group-label">${group.name}</div>${group.items.map(item => `<button class="run-card" data-run="${h(item.run_id)}"><div class="run-card-top"><span class="run-icon">${icon.layers}</span><span class="run-state">RECORDED</span></div><strong>${h(item.title)}</strong><span class="run-card-meta">${nativeTest(item.run_id) ? `Test ${h(nativeTest(item.run_id))} · ` : ""}${format(item.metadata.duration_ms)} ms · seed ${h(item.metadata.seed)}</span><div class="run-card-bottom"><span>${format(item.metadata.spike_events)} spike${item.metadata.spike_events === 1 ? '' : 's'}</span>${icon.chevron}</div></button>`).join('')}`).join('');
  document.querySelectorAll<HTMLButtonElement>('[data-run]').forEach(button => button.addEventListener('click', () => void selectRun(button.dataset.run!).catch(error => {
    document.querySelector('#live-status')!.textContent = `Could not load recorded run: ${error instanceof Error ? error.message : error}`;
    document.querySelector('#run-title')!.textContent = 'Replay unavailable; choose another recorded run.';
  })));
}

async function selectRun(id: string): Promise<void> {
  const token = ++loadingToken;
  setPlaying(false);
  const summary = index.runs.find(item => item.run_id === id)!;
  const next = cache.get(id) ?? await get<Replay>(summary.file);
  if (token !== loadingToken) return;
  if (!next.recorded_simulation || !Number.isFinite(next.metadata.duration_ms) || next.metadata.duration_ms <= 0 || next.graph.nodes.some(node => typeof node.id !== 'string')) throw new Error('Invalid recorded replay or neuron ID encoding.');
  cache.set(id, next); run = next; currentTime = 0; activeMode = 'neural';
  scene?.load(run);
  document.querySelector<HTMLDivElement>('.legend')!.dataset.mode = '';
  document.querySelectorAll<HTMLButtonElement>('[data-run]').forEach(button => { button.classList.toggle('selected', button.dataset.run === id); button.setAttribute('aria-pressed', String(button.dataset.run === id)); });
  document.querySelector('#run-title')!.textContent = run.title;
  const timeline = document.querySelector<HTMLInputElement>('#timeline')!;
  timeline.max = String(run.metadata.duration_ms); timeline.step = String(run.metadata.timestep_ms ?? 0.1); timeline.value = '0';
  document.querySelector('#duration-value')!.textContent = `${format(run.metadata.duration_ms)} ms`;
  document.querySelector('#spike-count')!.textContent = format(run.metadata.spike_events);
  document.querySelector('#active-count')!.textContent = format(run.metadata.active_neurons);
  document.querySelector('#chart-range')!.textContent = `${format(run.activity.histogram.bin_width_ms)} ms bins · ${run.activity.histogram.complete ? 'all events counted' : 'partial preview'}`;
  document.querySelector('#run-context')!.innerHTML = `<span class="eyebrow">${run.metadata.native_trace_verified ? 'VERIFIED NATIVE OMNIGENT RUN' : science(run) ? 'MODEL EXPERIMENT' : 'TECHNICAL SETUP CHECK'}</span><h3>${science(run) ? 'What does this input change?' : 'Does the full network execute?'}</h3><p>${h(run.metadata.question ?? (science(run) ? 'Compare recorded neural responses under matched stimulation and control conditions.' : index.technical_setup_check?.question))}</p><div class="scope-tag">${run.metadata.full_network_included ? 'Whole downloaded v783 graph' : 'Check run scope in metadata'}</div>`;
  document.querySelector('#run-insight')!.innerHTML = `<div class="insight"><span class="eyebrow">${run.metadata.readout_metrics ? 'PREDEFINED DNg02 READOUT' : 'WHAT THIS RUN TELLS US'}</span>${run.metadata.readout_metrics ? `<div class="readout-value">${format(run.metadata.readout_metrics.population_mean_rate_hz)} <small>Hz / cell</small></div><p>All ${run.metadata.readout_neuron_ids?.length ?? 25} selected cells count, including zero-spike cells.</p>` : `<p>${h(science(run) ? run.metadata.evidence_scope : 'The model responds to a generic input. This is a runtime check; it does not identify a biological function.')}</p>`}</div><div class="body-status"><span class="status-dot ${run.body?.states?.length ? '' : 'off'}"></span><span>${run.body?.states?.length ? run.body.published_policy ? 'Published policy + neural modulation' : 'Real body physics replay available' : 'No body trajectory linked to this run'}<small>${run.body?.states?.length ? `${format(run.body.duration_ms)} ms ${run.body.task_terminated_early ? '· terminated early' : '· full recorded horizon'}. ${run.body.published_policy ? 'Trained policy supplies stabilization; neural input stays open loop.' : 'Approximate wing controller; no stable-flight claim.'}` : 'No movement or flight result is inferred.'}</small></span></div>`;
  const bodyButton = document.querySelector<HTMLButtonElement>('#body-mode')!; bodyButton.disabled = !run.body?.states?.length;
  document.querySelector('#neural-mode')!.classList.add('active'); document.querySelector('#neural-mode')!.setAttribute('aria-pressed', 'true'); bodyButton.classList.remove('active'); bodyButton.setAttribute('aria-pressed', 'false');
  document.querySelector('#scene-label')!.textContent = 'Abstract layout · real neuron IDs';
  const neurons = [...run.graph.nodes].sort((a, b) => Number(b.target) - Number(a.target) || b.spike_count - a.spike_count);
  document.querySelector('#neuron-select')!.innerHTML = neurons.map(node => `<option value="${h(node.id)}">${node.target ? 'TARGET ' : ''}${h(short(node.id))} · ${node.spike_count} spikes</option>`).join('');
  selectNeuron(neurons[0]?.id ?? '');
  (document.querySelector('#raw-link') as HTMLAnchorElement).href = run.provenance.run_record_url;
  selectTab(activeTab);
  updateTime();
  document.querySelector('#live-status')!.textContent = `Loaded ${run.title}. ${run.metadata.spike_events} recorded spike events, duration ${run.metadata.duration_ms} milliseconds.`;
}

function selectNeuron(id: string): void {
  scene?.select(id);
  const node = run?.graph.nodes.find(item => item.id === id);
  if (!node) return;
  document.querySelector<HTMLSelectElement>('#neuron-select')!.value = id;
  document.querySelector('#neuron-detail')!.innerHTML = `<code>${h(id)}</code><div><span>${node.target ? 'Stimulated target' : node.readout ? 'DNg02 readout cell' : 'Sampled model neuron'}</span><strong>${format(node.spike_count)} recorded spikes</strong></div><small>Identity preserved as a string. Layout gives no anatomical location${node.readout ? '; cell type follows the linked annotation evidence.' : ' or functional annotation.'}</small>`;
}

function setPlaying(value: boolean): void {
  playing = value;
  const button = document.querySelector<HTMLButtonElement>('#play');
  if (button) { button.innerHTML = playing ? icon.pause : icon.play; button.setAttribute('aria-label', playing ? 'Pause recorded simulation' : 'Play recorded simulation'); }
}

function selectTab(tab: typeof activeTab): void {
  activeTab = tab;
  document.querySelectorAll<HTMLButtonElement>('[role="tab"]').forEach(button => { const selected = button.id === `tab-${tab}`; button.setAttribute('aria-selected', String(selected)); button.tabIndex = selected ? 0 : -1; });
  const content = document.querySelector<HTMLDivElement>('#tab-content')!;
  content.setAttribute('aria-labelledby', `tab-${tab}`);
  if (!run) return;
  if (tab === 'results') content.innerHTML = results();
  if (tab === 'parameters') content.innerHTML = parameters();
  if (tab === 'evidence') content.innerHTML = sources(run.sources);
  if (tab === 'method') content.innerHTML = method();
  if (tab === 'trace') content.innerHTML = nativeTrace();
}

function matched(metadata: Metadata): boolean {
  const candidate = metadata as Metadata & { design_id?: string };
  const selected = run.metadata as Metadata & { design_id?: string };
  if (candidate.design_id || selected.design_id) return candidate.design_id === selected.design_id && candidate.seed === selected.seed && candidate.execution_context === selected.execution_context;
  if (metadata.experiment_id || run.metadata.experiment_id) return metadata.experiment_id === run.metadata.experiment_id;
  return metadata.duration_ms === run.metadata.duration_ms && metadata.seed === run.metadata.seed && JSON.stringify(metadata.stimulated_neuron_ids) === JSON.stringify(run.metadata.stimulated_neuron_ids);
}

function results(): string {
  const comparison = index.comparisons?.find(item => item.run_ids.includes(run.run_id));
  const controls = index.runs.filter(item => matched(item.metadata) && (!comparison || comparison.run_ids.includes(item.run_id)));
  const max = Math.max(1, ...controls.map(item => item.metadata.spike_events));
  const summary = !science(run) ? index.technical_setup_check?.interpretation : 'The table compares matched recorded model runs. Population spike counts describe model activity; they do not by themselves demonstrate a motor or biological function.';
  return `<div class="detail-top"><div><span class="eyebrow">OBSERVED RESPONSE</span><h3>${science(run) ? 'Same model. Controlled changes.' : '150 Hz input versus 0 Hz sham.'}</h3><p>${h(summary)}</p></div><div class="check-pill">${controls.length} matched runs · seed ${h(run.metadata.seed)}</div></div><div class="comparison-table-wrap"><table><thead><tr><th scope="col">Recorded condition</th><th scope="col">Stimulus</th>${science(run) ? '<th scope="col">DNg02 mean</th>' : ''}<th scope="col">Spike events</th><th scope="col">Active cells</th><th scope="col">Wall time</th></tr></thead><tbody>${controls.map(item => `<tr class="${item.run_id === run.run_id ? 'current-row' : ''}"><th scope="row">${h(item.title)}<small>Seed ${h(item.metadata.seed)} · ${format(item.metadata.duration_ms)} ms</small></th><td>${format(item.metadata.stimulus_rate_hz)} Hz</td>${science(run) ? `<td>${format(item.metadata.readout_metrics?.population_mean_rate_hz)} Hz/cell</td>` : ''}<td><div class="bar-cell"><b>${format(item.metadata.spike_events)}</b><span><i style="width:${item.metadata.spike_events / max * 100}%"></i></span></div></td><td>${format(item.metadata.active_neurons)}</td><td>${format(item.metadata.wall_seconds)} s</td></tr>`).join('')}</tbody></table></div>${comparison ? `<div class="pooled-result"><div><span class="eyebrow">POOLED ACROSS ${h(comparison.summary.n_seeds)} FIXED SEEDS</span><p>Driven DNg02 mean: <strong>${format(comparison.summary.upstream_drive?.mean_hz)} Hz/cell</strong>${comparison.summary.upstream_drive?.sample_sd_hz !== undefined ? ` · SD ${format(comparison.summary.upstream_drive.sample_sd_hz)}` : ''}. ${h(comparison.summary.inference)}</p><small>Execution context: ${h(comparison.execution_context)}${run.metadata.native_trace_verified ? ' · independently trace-verified' : ''}</small></div><div><span class="eyebrow">RESULT → UPDATED DECISION</span><p>${h(comparison.summary.updated_decision)}</p><a class="text-link" href="${link(comparison.url)}" target="_blank" rel="noopener">Full comparison record ${icon.arrow}</a></div></div>` : ''}${bodySummary()}<div class="result-caution">${science(run) ? 'Read the frozen design and target evidence before attributing a function. Run duration and recorded trials limit the conclusion.' : 'One seed, one trial, 20 ms. This technical comparison is insufficient for statistical or behavioral conclusions.'}</div>`;
}

function bodySummary(): string {
  const body = run.body;
  if (!body?.states?.length) return '';
  const pair = index.coupling?.paired_results.find(item => item.driven_run_id === body.run_id || item.sham_run_id === body.run_id);
  return `<div class="body-summary"><span class="eyebrow">SEPARATE BRAIN-TO-BODY PHYSICS RECORD</span><h4>${body.published_policy ? 'Published flight policy, with neural modulation.' : 'Approximate wing-pattern controller.'}</h4><p>${h(body.model)} · ${format(body.duration_ms)} ms recorded${body.task_terminated_early ? ', terminated early' : ', full bounded horizon; no early termination'}. Root displacement: ${format(body.metrics?.root_displacement_cm)} cm. Max adapter input: ${format(body.metrics?.maximum_adapter_rate_hz)} Hz.</p><p>${body.published_policy ? 'Stabilization comes from the authors’ independently trained policy. The fixed adapter applies recorded DNg02 activity to wing control. The body controller uses feedback; the neural network receives no sensory feedback.' : 'The fixed approximate controller supplies the wing pattern. There is no sensory feedback to the neural model.'} The mapping is biologically uncalibrated.</p>${pair ? `<div class="body-pair-metrics"><div><span>Matched sham/drive horizon</span><strong>${format(pair.common_horizon_ms)} ms</strong></div><div><span>Wing angle RMS difference</span><strong>${pair.wing_angle_rms_difference_rad.toPrecision(4)} rad</strong></div><div><span>Root pose difference at horizon</span><strong>${pair.root_position_difference_cm_at_common_horizon.toPrecision(4)} cm</strong></div></div>` : ''}<a class="text-link" href="${link(body.run_record_url ?? '')}" target="_blank" rel="noopener">Body run and adapter parameters ${icon.arrow}</a>${body.published_policy ? `<a class="text-link policy-source" href="${link(body.published_policy.source)}" target="_blank" rel="noopener">Authors’ published policy ${icon.arrow}</a>` : ''}${run.body_variants && run.body_variants.length > 1 ? `<details class="body-history"><summary>Earlier controller diagnostics (${run.body_variants.length - 1})</summary>${run.body_variants.filter(item => item.run_id !== body.run_id).map(item => `<a href="${link(item.run_record_url ?? '')}" target="_blank" rel="noopener">${h(item.controller)} · ${format(item.duration_ms)} ms${item.task_terminated_early ? ' · early termination' : ''} ${icon.arrow}</a>`).join('')}</details>` : ''}</div>`;
}

function nativeTrace(): string {
  const discovery = index.discovery;
  if (!discovery?.verified) return '<div class="detail-top"><div><span class="eyebrow">EXECUTION PROVENANCE</span><h3>No verified native trace in this export.</h3><p>The recorded neural experiments remain available. Their results alone do not establish an Omnigent discovery loop.</p></div></div>';
  const traces = [discovery, ...(discovery.followup_traces ?? [])];
  const receipt = discovery.receipts.find(item => item.run_ids.includes(run.run_id)) ?? discovery.receipts[0];
  const selectedTrace = traces.find(item => item.own_receipt_ids?.includes(receipt?.receipt_id))
    ?? [...traces].reverse().find(item => item.receipts.some(candidate => candidate.run_ids.includes(run.run_id))) ?? discovery;
  const record = discovery.analyst_records.filter(item => item.tool_receipt_ids.includes(receipt?.receipt_id)).at(-1) ?? discovery.analyst_records.at(-1);
  const descriptions: Record<string, [string, string]> = {
    researcher: ['Research', 'Read stored primary-evidence snapshots; preserve source and claim IDs.'],
    evidence_reviewer: ['Evidence review', 'Check v783 identities and narrow the biological claims. Source-read limits are retained in the output.'],
    hypothesis_planner: ['Test selection', receipt?.test === 'B' ? 'Read the preceding A result; select the outgoing-disconnection control as the next test.' : 'Compare A stimulation versus sham with B outgoing disconnection; select A first.'],
    experimenter: ['Numerical experiment', 'Execute a new frozen comparison and return its real receipt and raw run paths.'],
    analyst: ['Result and next decision', 'Read the actual result, apply the frozen branch rule and save the next experiment.'],
  };
  const completedTests = [...new Set(discovery.receipts.map(item => item.test))];
  const followups = traces.filter(item => item !== selectedTrace);
  const crossSessionProof = traces.flatMap(item => item.cross_session_followup_proofs ?? []).map(proof => `<div class="followup-trace cross-session-proof"><span class="eyebrow">RESULT-DEPENDENT FOLLOW-UP · TWO DISTINCT ROOTS</span><h4>A’s saved decision was read before B was planned.</h4><p>The preceding A tree was reverified, including its numerical receipt and analyst record. B’s supervisor read that exact record before dispatching its planner and experimenter. These are separate native sessions.</p><div class="proof-order"><span>Read A decision <strong>position ${proof.current_record_read.result_position}</strong></span>${icon.chevron}<span>Dispatch B planner <strong>position ${proof.current_planner_launch_position}</strong></span>${icon.chevron}<span>Dispatch B experimenter <strong>position ${proof.current_experimenter_launch_position}</strong></span></div><p>Positions refer to the persisted B root history; they are not elapsed times.</p><div class="trace-links"><a class="text-link" href="${link(proof.prior_trace_url)}" target="_blank" rel="noopener">Preceding verified A trace ${icon.arrow}</a><a class="text-link" href="${link(proof.prior_record_url)}" target="_blank" rel="noopener">Exact A decision read by B ${icon.arrow}</a></div><details><summary>Inspect cross-session proof identifiers</summary><div class="handoff-proof"><span>Preceding A root</span><code>${h(proof.prior_root_conversation_id)}</code><span>Current B root</span><code>${h(proof.current_root_conversation_id)}</code><span>A decision record</span><code>${h(proof.prior_record_id)}</code><span>A decision / read content SHA-256</span><code>${h(proof.prior_record_sha256)}</code><span>A native trace SHA-256</span><code>${h(proof.prior_trace_sha256)}</code><span>Actual B read call</span><code>${h(proof.current_record_read.call_id)}</code><span>Native read result SHA-256</span><code>${h(proof.current_record_read.result_item_sha256)}</code><span>Fresh B numeric receipt</span><code>${h(proof.current_receipt_id)}</code></div></details></div>`).join('');
  return `<div class="detail-top"><div><span class="eyebrow">VERIFIED NATIVE DISCOVERY LOOP</span><h3>Test ${h(receipt?.test)}. Five collected specialists.</h3><p>Omnigent ${h(selectedTrace.omnigent_version)} dispatched and collected these native specialist handoffs. The numerical receipt and analyst decision were checked independently against the sealed design and raw artifacts.</p><p class="trace-root">This test’s root session: <code>${h(selectedTrace.root_conversation_id)}</code></p></div><a class="text-link" href="${link(selectedTrace.trace_url)}" target="_blank" rel="noopener">Full native trace ${icon.arrow}</a></div>${!run.metadata.native_trace_verified ? '<p class="result-caution">The selected run is outside this verified trace. Its original execution context remains separate; the handoffs below prove only their linked fresh native runs.</p>' : ''}<div class="trace-metrics"><div><span>Collected handoffs · ${traces.length} root session${traces.length === 1 ? "" : "s"}</span><strong>${traces.reduce((total, item) => total + item.stages.length, 0)}</strong></div><div><span>Fresh native neural runs</span><strong>${discovery.verified_run_ids.length}</strong></div><div><span>Selected test ${h(receipt?.test)} · numeric tool runtime</span><strong>${receipt?.wall_seconds.toFixed(4)} <small>s</small></strong></div></div><ol class="handoff-list">${selectedTrace.stages.map((stage, stageIndex) => `<li><div class="handoff-order">${String(stageIndex + 1).padStart(2, '0')}</div><div class="handoff-content"><div class="handoff-heading"><h4>${h(descriptions[stage.role]?.[0] ?? stage.role)}</h4><span>COLLECTED & VERIFIED</span></div><p>${h(descriptions[stage.role]?.[1] ?? '')}</p><div class="handoff-tools"><span>Observed tools:</span> ${h(stage.observed_tools.join(', ') || 'structured planning handoff')}</div><details><summary>Inspect native output and proof identifiers</summary><div class="handoff-proof"><span>Session</span><code>${h(stage.conversation_id)}</code><span>Final output SHA-256</span><code>${h(stage.final_item_sha256)}</code><span>Parent inbox result SHA-256</span><code>${h(stage.inbox_result_item_sha256)}</code></div><pre>${h(stage.output_excerpt)}</pre>${stage.excerpt_truncated ? '<small>Excerpt truncated; the linked trace contains the complete persisted output.</small>' : ''}</details></div></li>`).join('')}</ol>${followups.map(followup => `<div class="followup-trace"><span class="eyebrow">OTHER VERIFIED NATIVE SESSION</span><h4>Test ${h(followup.receipts.filter(item => !followup.own_receipt_ids || followup.own_receipt_ids.includes(item.receipt_id)).map(item => item.test).join(", "))} · ${followup.stages.length} collected specialist roles</h4><p>Separate root session <code>${h(followup.root_conversation_id)}</code>. These fresh receipts and decisions were verified in their own native trace.</p><a class="text-link" href="${link(followup.trace_url)}" target="_blank" rel="noopener">Other verified native trace ${icon.arrow}</a><details><summary>Inspect other session handoff identifiers</summary>${followup.stages.map(stage => `<div class="handoff-proof"><span>${h(stage.role)} session</span><code>${h(stage.conversation_id)}</code><span>Final output SHA-256</span><code>${h(stage.final_item_sha256)}</code><span>Inbox result SHA-256</span><code>${h(stage.inbox_result_item_sha256)}</code></div>`).join("")}</details></div>`).join("")}${crossSessionProof}<div class="trace-decision"><span class="eyebrow">OBSERVED RESULT → SAVED NEXT DECISION</span><h4>${h(record?.updated_decision)}</h4><p>${h(record?.decision_reason)}</p><p class="trace-next">Verified native tests in this snapshot: <strong>${h(completedTests.join(', '))}</strong>. ${record?.next_test === 'B' && !completedTests.includes('B') ? 'B was selected as the next experiment; no verified native B execution is claimed by this snapshot. Independent B feasibility runs are labeled separately.' : record?.next_test === "B" && completedTests.includes("B") ? "This A decision selected B; its separately verified follow-up is available in this snapshot." : `Saved next test: ${h(record?.next_test?.replaceAll("_", " "))}.`}</p><div class="trace-links"><a class="text-link" href="${link(receipt?.url ?? '')}" target="_blank" rel="noopener">Numeric receipt ${icon.arrow}</a><a class="text-link" href="${link(record?.url ?? '')}" target="_blank" rel="noopener">Saved analyst decision ${icon.arrow}</a><a class="text-link" href="${link(receipt?.comparison_url ?? '')}" target="_blank" rel="noopener">Six-run comparison ${icon.arrow}</a></div><code>${h(receipt?.receipt_id)}</code><code>${h(record?.record_id)}</code></div><div class="trace-scope"><p><strong>Evidence route:</strong> ${h(selectedTrace.evidence_mode)}. The native chain used the existing source snapshots; this is not a new BrightData crawl.</p><p><strong>Audit limits:</strong> ${h(selectedTrace.verification_scope)} ${selectedTrace.unsuccessful_tool_output_count} unsuccessful tool outputs are retained in the source trace. Saved analyst records preserve their original pre-audit status; the independent trace is the later verification layer.</p><div class="fingerprints"><div><span>Trace SHA-256</span><code>${h(selectedTrace.trace_sha256)}</code></div><div><span>Sealed design SHA-256</span><code>${h(receipt?.design_sha256)}</code></div></div></div>`;
}

function parameters(): string {
  const m = run.metadata;
  const params = [ ['Dataset', m.dataset_version], ['Model', 'Shiu whole-brain LIF'], ['Simulated duration', `${format(m.duration_ms)} ms`], ['Time step', `${format(m.timestep_ms)} ms`], ['Poisson stimulation', `${format(m.stimulus_rate_hz)} Hz`], ['Seed / trials', `${m.seed} / ${m.n_trials}`], ['Neurons included', format(m.neurons)], ['Connection rows', format(m.connection_rows)], ['Backend', m.backend ?? 'See raw record'], ['Compute wall time', `${format(m.wall_seconds)} s`], ['Linked body replay', run.body?.states?.length ? 'Separate open-loop physics run' : 'None'], ['Execution context', m.execution_context ?? 'Independent technical check'], ['Started (UTC)', m.started_at_utc] ];
  return `<div class="detail-top"><div><span class="eyebrow">REPRODUCIBILITY</span><h3>Inspect the recorded configuration.</h3><p>Each replay links to its original run record and immutable source fingerprint.</p></div><a href="${link(run.provenance.spike_source_url)}" target="_blank" rel="noopener" class="text-link">Raw spike data ${icon.arrow}</a></div><dl class="parameter-grid">${params.map(([label, value]) => `<div><dt>${h(label)}</dt><dd>${h(value)}</dd></div>`).join('')}</dl><div class="fingerprints"><div><span>Stimulation IDs</span><code>${h(m.stimulated_neuron_ids.join(', '))}</code></div><div><span>Author model commit</span><code>${h(m.model_commit)}</code></div><div><span>Run record SHA-256</span><code>${h(run.provenance.run_record_sha256)}</code></div><div><span>Spike output SHA-256</span><code>${h(run.provenance.spike_source_sha256)}</code></div></div>`;
}

function sources(items: Source[]): string {
  return `<div class="detail-top"><div><span class="eyebrow">SOURCE-BASED, WITH LIMITS</span><h3>Follow the evidence back to its origin.</h3><p>The connectome, dynamical model and biological claims are separate evidence layers.</p></div></div><div class="source-grid">${items.map(source => `<a class="source-card" href="${link(source.url)}" target="_blank" rel="noopener"><span class="eyebrow">${h(source.kind ?? 'SOURCE')}</span><h4>${h(source.title)} ${icon.arrow}</h4><p>${h(source.scope ?? '')}</p></a>`).join('')}</div><p class="detail-note">Connectome attribution: FlyWire Consortium (2024), v783 · CC BY 4.0. The model-ready tables are transformed by the Shiu author implementation. Neural anatomical coordinates are not included in this viewer.</p>`;
}

function method(): string {
  const limitations = run.metadata.limitations ?? [];
  return `<div class="method-grid"><div><span class="eyebrow">SIMULATION & DISPLAY ARE DIFFERENT</span><h3>What this replay represents.</h3><p>${h(run.metadata.evidence_scope)}</p>${run.metadata.hypothesis ? `<div class="hypothesis"><strong>Frozen, model-generated hypothesis</strong><p>${h(run.metadata.hypothesis)}</p></div>` : ''}<dl><dt>Simulation scope</dt><dd>${run.metadata.full_network_included ? 'All 138,639 neurons in the downloaded model-ready v783 graph.' : 'See original run record for exact subset.'}</dd><dt>3D display</dt><dd>${h(run.graph.selection)}. ${h(run.graph.layout)}.</dd><dt>Time and sampling</dt><dd>Time is measured in milliseconds. Playback stretches ${format(run.metadata.duration_ms)} ms to ${playbackSeconds} seconds. ${run.activity.events_complete ? 'Individual events are complete.' : `Individual events are sampled (${h(run.activity.display_sampling)}).`} Histogram counts ${run.activity.histogram.complete ? 'use the complete spike file' : 'use only the available preview'}.</dd><dt>Body and sensor feedback</dt><dd>${run.body?.states?.length ? `${h(run.body.model)}; controller ${h(run.body.controller)}; adapter ${h(typeof run.body.adapter === 'object' ? run.body.adapter?.adapter_id : run.body.adapter)}; ${h(run.body.loop)}. View reconstructs the author Flybody meshes using recorded root position, orientation and six wing angles. Other joints remain at the model reference pose. Camera following changes only the view; one scene unit = one centimeter, z-up. The body ${run.body.task_terminated_early ? `stops at early termination (${format(run.body.duration_ms)} ms)` : `completes its recorded ${format(run.body.duration_ms)} ms horizon`}; movement is never extrapolated. ${run.body.published_policy ? "The authors’ published trained policy supplies stabilization and closes body feedback; the neural network receives no sensory feedback." : "This approximate wing controller has no validated stable-flight result."}` : 'No body dynamics, motor adapter, flight or sensor feedback is inferred from this neural run.'}</dd><dt>Execution provenance</dt><dd>${h(run.metadata.execution_context ?? 'Independent technical smoke check')}. A recorded neural output alone does not establish that Omnigent orchestrated its execution; verify the linked discovery trace.</dd></dl></div><div><span class="eyebrow">LIMITS TO THE CONCLUSION</span><ul class="limitations">${[...limitations, ...(run.body?.limitations ?? [])].map(limit => `<li>${h(limit)}</li>`).join('')}</ul><div class="adjustments"><h4>Recorded implementation adjustments</h4>${[...(run.metadata.compatibility_adjustments ?? []), ...(run.metadata.data_loading_adjustments ?? [])].map(value => `<p>${h(value)}</p>`).join('') || '<p>See the original record.</p>'}</div><a class="text-link" href="${REPO}/tree/main/agents" target="_blank" rel="noopener">Omnigent agents and policies ${icon.arrow}</a></div></div>`;
}

function updateTime(): void {
  if (!run) return;
  document.querySelector('#time-value')!.textContent = `${currentTime.toFixed(1)} ms`;
  document.querySelector<HTMLInputElement>('#timeline')!.value = String(currentTime);
  document.querySelector('#scene-label')!.textContent = activeMode === 'neural' ? 'Abstract layout · real neuron IDs' : `${scene?.bodyCaption() ?? 'Recorded body pose · cm, z-up'}${currentTime > (run.body?.duration_ms ?? Infinity) ? ` · stopped at ${format(run.body?.duration_ms)} ms (early termination)` : ''}`;
  const bodyCamera = document.querySelector<HTMLButtonElement>('#body-camera')!;
  bodyCamera.hidden = activeMode !== 'body'; bodyCamera.setAttribute('aria-pressed', String(scene?.isFollowingBody() ?? true));
  const legend = document.querySelector<HTMLDivElement>('.legend')!;
  if (legend.dataset.mode !== activeMode) {
    legend.dataset.mode = activeMode;
    legend.innerHTML = activeMode === 'body' ? `<span><i class="lime"></i>Recorded root + wing pose</span><span><i class="muted"></i>Complete measured trajectory</span><span>Model reference pose for other joints</span><span>1 scene unit = 1 cm</span><span>${run.body?.task_terminated_early ? "Early termination" : "Full bounded horizon"} · no extrapolation</span>` : `<span><i class="lime"></i>Stimulated target</span>${run.metadata.readout_neuron_ids?.length ? '<span><i class="teal"></i>DNg02 readout</span>' : ''}<span><i class="white"></i>Recorded spike</span><span><i class="muted"></i>Sampled model cell</span><span id="sample-count">${run.graph.nodes.length} IDs shown / ${format(run.metadata.neurons)} simulated</span>`;
  }
  chart();
}

function chart(): void {
  const canvas = document.querySelector<HTMLCanvasElement>('#activity-chart')!;
  const context = canvas.getContext('2d'); if (!context || !run) return;
  const width = canvas.clientWidth, height = canvas.clientHeight, ratio = Math.min(window.devicePixelRatio, 2);
  if (canvas.width !== Math.round(width * ratio) || canvas.height !== Math.round(height * ratio)) { canvas.width = Math.round(width * ratio); canvas.height = Math.round(height * ratio); }
  context.setTransform(ratio, 0, 0, ratio, 0, 0); context.clearRect(0, 0, width, height);
  const counts = run.activity.histogram.counts, max = Math.max(1, ...counts);
  context.strokeStyle = '#294144'; context.lineWidth = 1;
  for (let row = 1; row < 4; row++) { context.beginPath(); context.moveTo(0, height / 4 * row); context.lineTo(width, height / 4 * row); context.stroke(); }
  counts.forEach((count, bin) => { const x = bin / counts.length * width; context.fillStyle = bin * run.activity.histogram.bin_width_ms <= currentTime ? '#d5f78c' : '#526962'; context.fillRect(x, height - Math.max(count ? 3 : 0, count / max * (height - 6)), Math.max(1, width / counts.length - 2), Math.max(count ? 3 : 0, count / max * (height - 6))); });
  const x = currentTime / run.metadata.duration_ms * width; context.strokeStyle = '#f2f4ed'; context.beginPath(); context.moveTo(x, 0); context.lineTo(x, height); context.stroke();
  canvas.setAttribute('aria-label', `${run.metadata.spike_events} recorded spikes across ${run.metadata.duration_ms} milliseconds; ${counts.length} time bins. Current replay time ${currentTime.toFixed(1)} milliseconds.`);
}

function animate(timestamp: number): void {
  if (run && playing && lastFrame) { currentTime += Math.min(100, timestamp - lastFrame) / 1000 * run.metadata.duration_ms / playbackSeconds; if (currentTime >= run.metadata.duration_ms) { currentTime = run.metadata.duration_ms; setPlaying(false); } updateTime(); }
  lastFrame = timestamp;
  scene?.render(currentTime);
  requestAnimationFrame(animate);
}

async function start(): Promise<void> {
  frameShell();
  index = await get<ReplayIndex>('index.json');
  if (!index.runs?.length || index.schema_version !== 1) throw new Error('No recorded runs available in this export.');
  library();
  const initial = index.runs.find(item => item.run_id === index.default_run_id) ?? [...index.runs].reverse().find(item => item.metadata.native_trace_verified && item.metadata.condition === 'upstream_drive' && item.metadata.seed === 42) ?? index.runs.find(item => item.body_available && item.metadata.condition === 'upstream_drive') ?? [...index.runs].reverse().find(item => science(item) && item.metadata.condition === 'upstream_drive') ?? index.runs.find(item => item.metadata.stimulus_rate_hz > 0) ?? index.runs[0];
  await selectRun(initial.run_id);
  if (new URLSearchParams(location.search).get('view') === 'body' && run.body?.states?.length) document.querySelector<HTMLButtonElement>('#body-mode')!.click();
  window.addEventListener('resize', chart);
  requestAnimationFrame(animate);
}

  void start().catch(error => { document.querySelector('#run-list')!.innerHTML = `<div class="error-message"><strong>Replay could not be loaded.</strong><p>${h(error instanceof Error ? error.message : error)}</p><a href="${REPO}">Inspect the public run records</a></div>`; document.querySelector('#live-status')!.textContent = 'Replay data failed to load. Public run records are linked.'; });
