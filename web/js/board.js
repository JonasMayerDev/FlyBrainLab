// Expert board page: hypothesis, behaviour repertoire, board members, round-by-round discussion, results table.
// Data: data/board.json, exported from the recorded research sessions by `python3 -m flylab.board export`.

import { renderSimple } from './simple.js';

const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const label = (s) => String(s ?? '–').replace(/_/g, ' ');
const fmt = (x, d = 1) => (x === null || x === undefined || Number.isNaN(+x) ? '–' : (+x).toFixed(d));
const time = (ts) => (ts ? String(ts).slice(11, 16) : '');

const STATUS = {
  reproduced_body: ['Reproduced in body', 'an independent body run agreed with the paper and the movement verifier did not object'],
  reproduced_brain: ['Brain / adapter only', 'matches the paper only as a brain read-out or as a check of the hand-designed bridge'],
  conflict: ['Conflict', 'at least one simulated result disagrees with the published experiment'],
  untested: ['Untested', 'no stimulus from the literature has been replayed for this behaviour yet'],
};
const TYPE_LABEL = {
  question: 'research question', note: 'note', evidence: 'evidence', hypothesis: 'hypothesis',
  experiment_options: 'test designs', experiment_choice: 'choice', approval: 'approval gate',
  experiment_result: 'experiment result', movement_verification: 'movement check', analysis: 'analysis',
  decision: 'decision', board_statement: 'position', prior_review: 'reviewed earlier results',
};
const cites = (ex) => ex.used_by.filter((u) => u.type !== 'prior_review');
const KEY_TYPES = new Set(['question', 'hypothesis', 'experiment_options', 'experiment_choice', 'experiment_result',
  'movement_verification', 'decision', 'board_statement', 'prior_review']);

const state = { board: null, experts: {}, session: null, agent: '', keyOnly: false, open: new Set(), userPicked: false, seenLive: new Set() };
const POLL_MS = 4000;

// ---------------------------------------------------------------- small renderers

function md(text) {
  // Minimal, safe markdown for agent text: escape first, then headings, bold, bullet lists, paragraphs.
  const lines = esc(text).split('\n');
  let html = '', inList = false;
  for (let raw of lines) {
    const line = raw.trim();
    const li = /^[-*•]\s+(.*)/.exec(line);
    if (li) { if (!inList) { html += '<ul>'; inList = true; } html += `<li>${li[1]}</li>`; continue; }
    if (inList) { html += '</ul>'; inList = false; }
    if (!line) continue;
    const h = /^#{1,6}\s+(.*)/.exec(line);
    html += h ? `<p><b>${h[1]}</b></p>` : `<p>${line}</p>`;
  }
  if (inList) html += '</ul>';
  return html.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/\b(10\.\d{4,9}\/[^\s<),;]+)/g,
    (m) => `<a href="https://doi.org/${m}" target="_blank" rel="noopener">${m}</a>`);
}

const avatar = (id) => {
  const e = state.experts[id] || { name: id, color: '#888' };
  const ini = e.name.split(/\s+/).map((w) => w[0]).join('').slice(0, 2).toUpperCase();
  return `<span class="av" style="--c:${esc(e.color)}" aria-hidden="true">${esc(ini)}</span>`;
};
const refChip = (ref) => `<button type="button" class="ref" data-ref="${esc(ref)}" title="Jump to result ${esc(ref)}">↩ ${esc(ref)}</button>`;
const verdictPill = (v) => (v ? `<span class="pill v-${esc(v)} ${esc(v)}">${esc(label(v))}</span>` : '');
const stChip = (s) => `<span class="st-chip st-${esc(s)}" title="${esc(STATUS[s]?.[1] || '')}">${esc(STATUS[s]?.[0] || s)}</span>`;
const doiLink = (doi, text) => (doi ? `<a href="https://doi.org/${esc(doi)}" target="_blank" rel="noopener">${esc(text || 'doi:' + doi)}</a>` : '');

function stimulus(ex) {
  const exc = ex.excite.length > 4 ? `${ex.excite.slice(0, 4).join(', ')} +${ex.excite.length - 4}` : ex.excite.join(' + ');
  return `${esc(exc || 'none')}${ex.silence.length ? ` <span class="muted">silenced</span> <b>${esc(ex.silence.join(', '))}</b>` : ''}`;
}
function readout(ex) {
  if (ex.kind === 'screen') {
    const hits = Object.entries(ex.hits_by_target || {}).map(([t, h]) => `${esc(t)}: ${h.length}/${ex.excite.length}`).join(' · ');
    return `hits ≥ 5 Hz: ${hits || '–'}`;
  }
  const r = Object.entries(ex.readout_hz || {}).map(([k, v]) => `${esc(k)} ${fmt(v, 0)} Hz`).join(', ');
  return r || '<span class="muted">no descending read-out active</span>';
}
function bodyResult(ex) {
  const b = ex.body;
  if (!b) return ex.kind === 'screen' ? '<span class="muted">brain screen</span>' : '<span class="muted">brain only (no body)</span>';
  if (ex.kind === 'embodied_flight') return `<b>${esc(label(b.behavior))}</b> <span class="muted">· max height ${fmt(b.max_height_mm)} mm</span>`;
  return `<b>${esc(label(b.behavior))}</b> <span class="muted">· ${fmt(b.forward_disp_mm)} mm, ${fmt(b.heading_change_deg, 0)}°</span>`;
}

// ---------------------------------------------------------------- sections

function renderHypothesis(b) {
  const cov = b.coverage, c = cov.counts;
  const n = cov.behaviors.length;
  const body = c.reproduced_body || 0, brain = c.reproduced_brain || 0, conflict = c.conflict || 0, untested = c.untested || 0;
  const nExp = b.experiments.length, nRounds = b.sessions.reduce((a, s) => a + s.rounds.filter((r) => r.title !== 'Final report').length, 0);
  const answer = body === n
    ? 'All catalogued behaviours are reproduced in the body. The next test is behaviours outside the catalogue.'
    : `Not yet. ${body} of ${n} catalogued behaviours are reproduced independently in a simulated body, ${brain} match only as a brain read-out or an adapter check, ${conflict} ${conflict === 1 ? 'is' : 'are'} in conflict with the literature${untested ? `, ${untested} untested` : ''}. ${cov.not_catalogued.length} real behaviours have no published stimulus in the lab's catalogue yet.`;
  $('#hypothesis').innerHTML = `
    <div>
      <h2 id="hyp-h" class="typ">Lab hypothesis</h2>
      <p class="q">${esc(b.hypothesis.en)}</p>
      <details><summary>Deutsch</summary><p>${esc(b.hypothesis.de)}</p></details>
      <p class="answer"><b>Answer so far:</b> ${esc(answer)}</p>
    </div>
    <div class="stats">
      <div class="stat"><b>${cov.n_impulses_tested}/${cov.n_impulses}</b><span>published stimuli replayed in silico</span></div>
      <div class="stat"><b>${nExp}</b><span>experiments run by the board (${b.sessions.length} sessions)</span></div>
      <div class="stat"><b>${nRounds}</b><span>discussion rounds with a decision</span></div>
      <div class="stat"><b>${b.experiments.filter((x) => cites(x).length).length}/${nExp}</b><span>results explicitly cited again in a later post</span></div>
    </div>`;
}

function renderRepertoire(cov) {
  const tests = (i) => i.tests.map((t) => `<span class="pill v-${esc(t.verdict)}" title="${esc(t.source)}${t.note ? ' – ' + esc(t.note) : ''}">${esc(label(t.verdict))} · ${esc(t.label_source)}${t.circular ? ' · adapter' : ''}${t.verifier ? ' · verifier ' + esc(t.verifier) : ''}</span>`).join('') || '<span class="pill">not tested yet</span>';
  $('#repertoire').innerHTML = cov.behaviors.map((b) => `
    <article class="panel rep st-${esc(b.status)}">
      <h3>${esc(b.label)}</h3>
      <div>${stChip(b.status)} <span class="where">· ${esc(b.body)} · ${b.n_tested}/${b.n_impulses} stimuli tested</span></div>
      <details><summary>Published stimuli (${b.n_impulses})</summary>
        ${b.impulses.map((i) => `<div class="imp">
          <div><b>${esc(label(i.manipulation))} ${esc(i.target)}</b> → ${esc(i.effect === 'reduce' ? 'reduces' : 'evokes')} ${esc(label(b.id))}
            <span class="muted">(${esc(i.citation.first_author)} et al. ${esc(i.citation.year)}, ${doiLink(i.citation.doi, 'doi')})</span></div>
          <div class="tests">${tests(i)}</div></div>`).join('')}
      </details>
    </article>`).join('') + `
    <div class="panel rep-gap"><b>Not catalogued yet</b> (no published stimulus in the lab's ground truth, so the board cannot test them): ${cov.not_catalogued.map(esc).join(' · ')}.</div>`;
}

function renderExperts(b) {
  $('#experts').innerHTML = b.experts.map((e) => `
    <button type="button" class="panel expert" data-agent="${esc(e.id)}" aria-pressed="${state.agent === e.id}">
      ${avatar(e.id)}
      <span class="who"><b>${esc(e.name)}</b><span class="disc">${esc(e.speaks_for)} · ${e.n_posts} posts</span>
      <span class="dec">${esc(e.decides)}</span></span>
    </button>`).join('');
  const sel = $('#f-agent');
  sel.innerHTML = '<option value="">all</option>' + b.experts.filter((e) => e.n_posts).map((e) => `<option value="${esc(e.id)}">${esc(e.name)}</option>`).join('');
  sel.value = state.agent;
}

function setAgent(a) {
  state.agent = a;
  $('#f-agent').value = a;
  document.querySelectorAll('.expert').forEach((x) => x.setAttribute('aria-pressed', String(x.dataset.agent === a)));
  renderDiscussion();
}

function renderSessions(b) {
  $('#sessions').innerHTML = b.sessions.map((s) => `
    <button type="button" role="tab" data-s="${esc(s.id)}" aria-selected="false">
      <b>${esc(s.id)}</b>${s.status === 'running' ? ' <span class="live-dot" title="running now">● live</span>' : ''} · ${esc(s.question)}<small>${esc(String(s.started).slice(0, 10))} ${time(s.started)}–${time(s.ended)} · ${s.rounds.length} rounds · ${s.n_events} record events</small>
    </button>`).join('');
}

function selectSession(id) {
  state.session = id;
  document.querySelectorAll('#sessions button').forEach((x) => x.setAttribute('aria-selected', String(x.dataset.s === id)));
  renderDiscussion();
}

function postExtras(p, nextChoice) {
  let h = '';
  if (p.hypothesis) {
    h += `<div class="kv"><span class="pill agent">agent-generated</span><span>predicts <b>${esc(label(p.hypothesis.predicted))}</b></span>
      <span>targets <b>${esc((p.hypothesis.targets || []).join(', '))}</b></span><span>confidence <b>${fmt(p.hypothesis.confidence, 2)}</b></span></div>`;
  }
  if (p.hits) {
    h += `<ul class="mini">${p.hits.map((x) => `<li>${esc(x.title)} (${esc(x.year)}) ${doiLink(x.doi)}</li>`).join('')}</ul>`;
  }
  if (p.ranking) {
    h += `<p class="mini muted">Connectome prior (prediction, not a result): ${p.ranking.map((r) => `${r.rank}. <b>${esc(r.cell_type)}</b> ${fmt(r.score, 0)}`).join(' · ')}</p>`;
  }
  if (p.options) {
    h += `<table class="opts mini"><tr><th>Test</th><th>Kind</th><th class="num">Cost</th><th class="num">Info gain</th><th>Why</th></tr>
      ${p.options.map((o) => `<tr class="${o.id === nextChoice ? 'chosen' : ''}"><td><b>${esc(o.id)}</b>${o.id === nextChoice ? ' ✓' : ''}</td><td>${esc(label(o.kind))}</td>
        <td class="num">${fmt(o.cost)}</td><td class="num">${esc(o.gain ?? '–')}</td><td>${esc(o.why)}</td></tr>`).join('')}</table>
      ${p.budget ? `<p class="mini muted">Budget per round: ${esc(p.budget)} cost units.</p>` : ''}`;
  }
  if (p.approval) {
    h += `<div class="box mini"><b>${esc(p.approval.status)}</b> · est. ${fmt(p.approval.cost)} units<br><span class="muted">${esc(p.approval.gate)}</span></div>`;
  }
  if (p.verification) {
    const v = p.verification;
    h += `<div class="kv"><span>expected <b>${esc(label(v.expected))}</b> <span class="muted">(${esc(v.source)})</span></span>
      <span>kinematics ${verdictPill(v.kinematic)}</span><span>blind vision ${verdictPill(v.vision)} <span class="muted">saw "${esc(label(v.vision_saw))}", conf ${fmt(v.vision_conf, 2)}</span></span>
      <span>final ${verdictPill(v.final)}</span></div>`;
  }
  if (p.comparison) {
    const c = p.comparison;
    h += `<div class="kv"><span>${esc(c.gt_id)}</span><span>expected <b>${esc(label(c.expected))}</b></span><span>observed <b>${esc(label(c.observed))}</b></span>
      ${verdictPill(c.verdict)}${c.surprise ? '<span class="pill uncertain">surprise</span>' : ''}${c.by_construction ? '<span class="pill">adapter by construction</span>' : ''}
      <span class="muted">label from ${esc(label(c.label_source))}</span></div>`;
  }
  if (p.decision) {
    const d = p.decision;
    if (d.reason) h += `<div class="box mini"><b>Because:</b> ${esc(d.reason)}</div>`;
    if (d.reopens_assumption) h += `<div class="box reopen mini"><b>Reopens assumption:</b> ${esc(d.reopens_assumption)}</div>`;
    if (d.next_step) h += `<p class="mini"><b>Next:</b> ${esc(d.next_step)}</p>`;
  }
  if (p.parallel) {
    h += `<p class="mini muted">${p.parallel.n} runs in parallel: wall ${fmt(p.parallel.wall_s)} s vs ${fmt(p.parallel.sum_s)} s summed (×${fmt(p.parallel.speedup, 2)}).</p>`;
  }
  if (p.reviewed && p.reviewed.length) h += `<p class="mini">Reviewed: ${p.reviewed.map(refChip).join(' ')}</p>`;
  return h;
}

function resultPost(p) {
  const ex = state.board.experiments.find((x) => x.id === p.result);
  if (!ex) return '';
  const ver = ex.verifications.map((v) => `${verdictPill(v.final)} <span class="muted">vs ${esc(label(v.expected))}</span>`).join(' ');
  const cmp = ex.comparisons.map((c) => `${verdictPill(c.verdict)} <span class="muted">${esc(c.gt_id)}</span>`).join(' ');
  return `<article class="panel post result" id="post-${esc(ex.id)}">${avatar(p.agent)}<div>
    <div class="meta"><b>Result ${esc(ex.id)}</b><span class="typ">${esc(label(ex.kind))}</span><span class="muted">${time(p.ts)}${ex.seed != null ? ' · seed ' + esc(ex.seed) : ''}${ex.runtime_s ? ' · ' + fmt(ex.runtime_s) + ' s' : ''}</span></div>
    <div class="kv"><span>stimulus: ${stimulus(ex)}</span></div>
    <div class="kv"><span>brain: ${readout(ex)}</span><span>body: ${bodyResult(ex)}</span></div>
    ${ver ? `<div class="kv"><span>movement verifier: ${ver}</span></div>` : ''}
    ${cmp ? `<div class="kv"><span>vs. literature: ${cmp}</span></div>` : ''}
    <div class="kv">${cites(ex).length ? `<span class="muted">cited in ${cites(ex).length} later post(s)</span>` : ''}
      <button type="button" class="more" data-row="${esc(ex.id)}">details ↓</button>
      ${ex.replay ? `<a class="mini" href="index.html#${esc(ex.replay.id)}" title="3D replay of the same stimulus, recomputed for the viewer (not this exact run)">3D replay (same stimulus) ↗</a>` : ''}</div>
  </div></article>`;
}

function renderDiscussion() {
  const b = state.board;
  const s = b.sessions.find((x) => x.id === state.session) || b.sessions[0];
  if (!s) { $('#discussion').innerHTML = '<p class="panel sess-note">No recorded session yet.</p>'; return; }
  const earlier = s.earlier_results_cited.length
    ? `This session cited ${s.earlier_results_cited.length} result(s) of earlier sessions: ${s.earlier_results_cited.map(refChip).join(' ')}`
    : (s.read_prior_sessions ? 'This session reviewed earlier sessions (see the first posts) but named none of their results.'
      : (s.id === b.sessions[0].id ? 'First session: no earlier results existed.'
        : 'This session did not read earlier sessions: the board review step (get_prior_results) was added after it ran. Rounds inside the session do build on each other.'));
  let html = `<div class="panel sess-note"><b>Question (human):</b> ${esc(s.question)}<br><span class="muted">${earlier}</span>
    <br><span class="muted mono">${esc(s.record)}</span></div>`;

  s.rounds.forEach((r, i) => {
    const posts = r.posts.filter((p) => (!state.agent || p.agent === state.agent) && (!state.keyOnly || KEY_TYPES.has(p.type) || p.comparison));
    const carry = r.carried_forward.length
      ? `<span>builds on</span> ${r.carried_forward.map(refChip).join(' ')}`
      : (i === 0 ? '<span>starts from the question and the literature</span>' : '<span>names no earlier result explicitly</span>');
    const reviewed = (r.reviewed_earlier || []).length ? `<span class="muted mini">· reviewed ${r.reviewed_earlier.length} earlier results</span>` : '';
    html += `<section class="round" aria-label="${esc(r.title)}"><header><h3>${esc(r.title)}</h3>
      <span class="muted mini">${r.experiments.length} experiment(s)</span><div class="carry">${carry}</div>${reviewed}</header>`;
    if (!posts.length) html += '<p class="muted mini">No posts match the filter in this round.</p>';
    posts.forEach((p) => {
      if (p.result) { html += resultPost(p); return; }
      const e = state.experts[p.agent] || { name: p.agent };
      const nextChoice = p.options ? (r.posts.find((q) => q.type === 'experiment_choice' && q.seq > p.seq)?.choice?.id) : null;
      const long = (p.text || '').length > 420;
      const key = `${s.id}-${p.seq}`;
      const clamp = long && !state.open.has(key);
      const refs = (p.refs || []).length ? `<div class="kv">${p.refs.map(refChip).join(' ')}</div>` : '';
      const isDecision = p.type === 'decision' && p.agent === 'supervisor';
      html += `<article class="panel post ${isDecision ? 'decision' : ''}" id="seq-${esc(s.id)}-${p.seq}">${avatar(p.agent)}<div>
        <div class="meta"><b>${esc(e.name)}</b><span class="typ">${esc(TYPE_LABEL[p.type] || label(p.type))}</span>
          ${p.stance ? `<span class="pill">${esc(p.stance)}</span>` : ''}<span class="muted">${time(p.ts)} · #${p.seq}</span></div>
        <div class="body ${clamp ? 'clamp' : ''}">${md(p.text)}</div>
        ${long ? `<button type="button" class="more" data-open="${esc(key)}">${clamp ? 'show more' : 'show less'}</button>` : ''}
        ${postExtras(p, nextChoice)}${refs}
        ${isDecision && i < s.rounds.length - 1 ? `<div class="next-arrow">→ carried into ${esc(s.rounds[i + 1].title)}</div>` : ''}
      </div></article>`;
    });
    html += '</section>';
  });
  if (s.status === 'running') {
    html += `<p class="panel sess-note live-note"><span class="live-dot">●</span> Session running: the board is still discussing. New posts appear here automatically (last record event ${s.last_event_age_s ?? '?'} s ago).</p>`;
  }
  $('#discussion').innerHTML = html;
}

function renderResults(b) {
  const head = '<tr><th>Result</th><th>Round</th><th>Stimulus</th><th>Brain read-out</th><th>Body</th><th>Verifier</th><th>vs. literature</th><th>Cited later</th></tr>';
  const rows = b.experiments.map((ex) => {
    const ver = ex.verifications.map((v) => verdictPill(v.final)).join(' ') || '<span class="muted">–</span>';
    const cmp = ex.comparisons.map((c) => verdictPill(c.verdict)).join(' ') || '<span class="muted">–</span>';
    return `<tr class="row" data-id="${esc(ex.id)}" tabindex="0" aria-expanded="false"><td><b>${esc(ex.id)}</b><br><span class="muted mini">${esc(label(ex.kind))}</span></td>
      <td>${esc(ex.session)} · R${esc(ex.round ?? '?')}</td><td>${stimulus(ex)}</td><td>${readout(ex)}</td><td>${bodyResult(ex)}</td>
      <td>${ver}</td><td>${cmp}</td><td class="num">${cites(ex).length}</td></tr>`;
  }).join('');
  $('#results').innerHTML = `<thead>${head}</thead><tbody>${rows}</tbody>`;
}

function detailRow(ex) {
  let h = `<p class="mini"><b>Record:</b> <span class="mono">runs/${esc(ex.run_id)}/record.jsonl</span> #${esc(ex.seq)} · ${esc(ex.summary)}</p>`;
  if (ex.screen) {
    const max = Math.max(1, ...ex.screen.flatMap((r) => Object.values(r.rates || {})));
    h += ex.screen.map((r) => Object.entries(r.rates || {}).map(([t, v]) =>
      `<div class="ratebar"><span>${esc(r.cell_type)} → ${esc(t)}</span><div class="bar"><span style="left:0;width:${(100 * v) / max}%"></span></div><span class="num">${fmt(v, 0)} Hz</span></div>`).join('')).join('');
  }
  if (ex.used_by.length) {
    h += `<p class="mini"><b>Cited by:</b> ${ex.used_by.map((u) => `<a href="#seq-${esc(u.session)}-${u.seq}" data-goto="${esc(u.session)}">${esc(u.session)} R${u.round} #${u.seq} ${esc(state.experts[u.agent]?.name || u.agent)} (${esc(TYPE_LABEL[u.type] || u.type)})</a>`).join(' · ')}</p>`;
  }
  if (ex.body && ex.body.label_warning) h += `<p class="mini muted">Label warning: ${esc(ex.body.label_warning)}</p>`;
  if (ex.body && ex.body.command) h += `<p class="mini">Flight command: ${Object.entries(ex.body.command).map(([k, v]) => `${esc(k)} ${fmt(v, 3)}`).join(' · ')}</p>`;
  if (ex.body && ex.body.drive) h += `<p class="mini">Walking drive: ${Object.entries(ex.body.drive).map(([k, v]) => `${esc(k)} ${fmt(v, 3)}`).join(' · ')}</p>`;
  return h;
}

function toggleRow(tr, force) {
  const open = force ?? tr.getAttribute('aria-expanded') !== 'true';
  const next = tr.nextElementSibling;
  if (next && next.classList.contains('detail-row')) next.remove();
  tr.setAttribute('aria-expanded', String(open));
  if (open) {
    const ex = state.board.experiments.find((x) => x.id === tr.dataset.id);
    tr.insertAdjacentHTML('afterend', `<tr class="detail-row"><td class="detail" colspan="8">${detailRow(ex)}</td></tr>`);
  }
}

function flash(el) {
  if (!el) return;
  el.scrollIntoView({ block: 'center' });
  el.classList.add('flash');
  setTimeout(() => el.classList.remove('flash'), 1600);
}

function gotoResult(id) {
  const ex = state.board.experiments.find((x) => x.id === id);
  if (!ex) return;
  if (state.session !== ex.session) selectSession(ex.session);
  const post = document.getElementById(`post-${id}`);
  if (post) { flash(post); return; }
  const tr = document.querySelector(`#results tr.row[data-id="${CSS.escape(id)}"]`);
  toggleRow(tr, true); flash(tr);
}

function wire() {
  document.querySelectorAll('.viewswitch button').forEach((x) => x.addEventListener('click', () => setView(x.dataset.view)));
  let saved = null;
  try { saved = localStorage.getItem('flylab-board-view'); } catch (e) { /* storage unavailable */ }
  setView(location.hash ? 'expert' : (saved || 'simple'));
  $('#sessions').addEventListener('click', (ev) => {
    const btn = ev.target.closest('button[data-s]'); if (btn) { state.userPicked = true; selectSession(btn.dataset.s); }
  });
  $('#experts').addEventListener('click', (ev) => {
    const btn = ev.target.closest('.expert'); if (!btn) return;
    setAgent(state.agent === btn.dataset.agent ? '' : btn.dataset.agent);
    $('#disc-h').scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
  $('#f-agent').addEventListener('change', (e) => setAgent(e.target.value));
  $('#f-key').addEventListener('change', (e) => { state.keyOnly = e.target.checked; renderDiscussion(); });
  document.addEventListener('click', (ev) => {
    const ref = ev.target.closest('[data-ref]');
    if (ref) { gotoResult(ref.dataset.ref); return; }
    const op = ev.target.closest('[data-open]');
    if (op) { const k = op.dataset.open; state.open.has(k) ? state.open.delete(k) : state.open.add(k); renderDiscussion(); return; }
    const row = ev.target.closest('[data-row]');
    if (row) { const tr = document.querySelector(`#results tr.row[data-id="${CSS.escape(row.dataset.row)}"]`); toggleRow(tr, true); flash(tr); return; }
    const go = ev.target.closest('[data-goto]');
    if (go) { ev.preventDefault(); selectSession(go.dataset.goto); flash(document.querySelector(go.getAttribute('href'))); return; }
    const tr = ev.target.closest('#results tr.row');
    if (tr) toggleRow(tr);
  });
  $('#results').addEventListener('keydown', (ev) => {
    const tr = ev.target.closest('tr.row');
    if (tr && (ev.key === 'Enter' || ev.key === ' ')) { ev.preventDefault(); toggleRow(tr); }
  });
  const themeBtn = $('#theme');
  const showTheme = () => {
    const mode = document.documentElement.dataset.theme || 'auto';
    themeBtn.textContent = mode[0].toUpperCase() + mode.slice(1);
    themeBtn.setAttribute('aria-label', `Colour theme: ${mode}`);
  };
  themeBtn.addEventListener('click', () => {
    const cur = document.documentElement.dataset.theme || 'auto';
    const next = { auto: 'light', light: 'dark', dark: 'auto' }[cur];
    if (next === 'auto') delete document.documentElement.dataset.theme; else document.documentElement.dataset.theme = next;
    try { if (next === 'auto') localStorage.removeItem('flylab-theme'); else localStorage.setItem('flylab-theme', next); } catch (e) { /* storage unavailable */ }
    showTheme();
  });
  showTheme();
}

async function main() {
  wire();
  try {
    const r = await fetch('data/board.json');
    if (!r.ok) throw new Error(`data/board.json: HTTP ${r.status} (run: python3 -m flylab.board export)`);
    const b = await r.json();
    renderAll(b);
    const want = decodeURIComponent(location.hash.slice(1));
    const live = b.sessions.find((x) => x.status === 'running');
    const last = live || b.sessions[b.sessions.length - 1];
    selectSession(last ? last.id : null);
    setTimeout(poll, POLL_MS);
    if (want && b.experiments.some((x) => x.id === want)) gotoResult(want);
    window.addEventListener('hashchange', () => gotoResult(decodeURIComponent(location.hash.slice(1))));
    showProv(b);
    window.__board = { state, ready: true };
  } catch (err) {
    console.error(err);
    $('#hypothesis').innerHTML = `<div class="error">Could not load the board data: ${esc(err.message)}</div>`;
    window.__board = { error: String(err) };
  }
}

function setView(v) {
  const simple = v !== 'expert';
  $('#simple-view').hidden = !simple;
  $('#main').hidden = simple;
  document.querySelectorAll('.viewswitch button').forEach((x) => x.setAttribute('aria-selected', String(x.dataset.view === (simple ? 'simple' : 'expert'))));
  try { localStorage.setItem('flylab-board-view', simple ? 'simple' : 'expert'); } catch (e) { /* storage unavailable */ }
}

function openExpert(sid) {
  setView('expert');
  selectSession(sid);
  $('#disc-h').scrollIntoView({ block: 'start' });
}

function renderAll(b) {
  state.board = b;
  for (const e of b.experts) state.experts[e.id] = e;
  const open = [...document.querySelectorAll('#simple-view details[open]')].map((d) => d.closest('.s-story')?.id);
  renderSimple(b, $('#simple-view'), openExpert);
  open.forEach((id) => { const d = id && document.querySelector(`#${CSS.escape(id)} details`); if (d) d.open = true; });
  renderHypothesis(b);
  renderRepertoire(b.coverage);
  renderExperts(b);
  renderSessions(b);
  renderResults(b);
  const live = b.sessions.filter((x) => x.status === 'running');
  const badge = $('.replay-badge');
  badge.classList.toggle('live', live.length > 0);
  badge.lastChild.textContent = live.length ? `Live session ${live.map((x) => x.id).join(', ')} running · updates every ${POLL_MS / 1000} s` : 'Recorded sessions · not live';
}

function showProv(b) {
  $('#prov').textContent = `exported ${String(b.generated).slice(0, 16).replace('T', ' ')} UTC · git ${b.git_rev || '?'} · ${b.skipped_runs.length} mock/empty run(s) excluded`;
}

async function poll() {
  try {
    const r = await fetch(`data/board.json?t=${Date.now()}`, { cache: 'no-store' });
    if (r.ok) {
      const b = await r.json();
      if (b.generated !== state.board.generated) {
        const y = window.scrollY;
        renderAll(b);
        const live = b.sessions.find((x) => x.status === 'running');
        // follow a newly started live session unless the viewer picked a session themselves
        if (live && !state.seenLive.has(live.id) && !state.userPicked) state.session = live.id;
        if (live) state.seenLive.add(live.id);
        selectSession(b.sessions.some((x) => x.id === state.session) ? state.session : b.sessions[b.sessions.length - 1]?.id);
        window.scrollTo(0, y);
        showProv(b);
      }
    }
  } catch (e) { /* offline or mid-write: try again next tick */ }
  setTimeout(poll, POLL_MS);
}

main();
