// Simple view of the expert board for non-experts: what we asked, how it works, what we found,
// and whether each experiment was done correctly (independent audit, flylab/audit.py).

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmt = (x, d = 0) => (x === null || x === undefined || Number.isNaN(+x) ? '–' : (+x).toFixed(d));

const VERDICT = {
  yes: ['good', 'Matches real flies'], brain: ['mid', 'Matches inside the brain'], partly: ['mid', 'Partly matches'],
  no: ['bad', 'Does not match'], open: ['none', 'Open'],
};
const MARK = { pass: ['good', '✓'], warn: ['mid', '!'], fail: ['bad', '✗'], 'n/a': ['none', '–'] };

let glossary = {};
const plainName = (g) => glossary[g] || glossary[String(g).replace(/_[LR]$/, '')] || (/^L[CT]|^LPLC|^MTe|^aMe/.test(g) ? `eye neurons (type ${g})` : g);

function verdictChip([cls, text]) { return `<span class="chip ${cls}">${esc(text)}</span>`; }

function hero(b) {
  const sc = b.brain_score, n = sc.counts;
  return `<section class="s-hero">
    <p class="kicker">Our question</p>
    <h2>Does the wiring diagram alone predict how a fly's brain responds?</h2>
    <p class="lead">Scientists have mapped all 139,000 nerve cells of a fruit fly's brain and every connection between them.
      We run that wiring as a computer model (the "brain copy") and give it the same nudges that scientists gave real flies in published experiments,
      for example switching on the eye neurons that see something approaching. Then we check: do the same <b>command neurons</b> switch on as in the real fly,
      such as the escape neuron that makes a fly jump away, while the others stay off? A board of AI experts plans each experiment, reads the result and decides what to test next.</p>
    <div class="s-answer">
      <div class="s-score"><span class="big">${n.agrees} of ${sc.n_conclusive}</span>
        <span>published experiments with a clear answer agree: the brain copy switched on the same command neurons as the real fly${n.depends ? `; ${n.depends} more agree only with strong stimulation` : ''}.</span></div>
      <ul class="s-tally">
        <li><span class="dot good"></span><b>${n.agrees}</b> agree</li>
        ${n.depends ? `<li><span class="dot mid"></span><b>${n.depends}</b> agree only with strong stimulation</li>` : ''}
        <li><span class="dot bad"></span><b>${n.disagrees}</b> disagree${n.disagrees ? ' (LPLC2: real flies also back away, the brain copy does not start backing away)' : ''}</li>
        <li><span class="dot none"></span><b>${n.unclear}</b> no clear answer</li>
        <li><span class="dot none"></span><b>${n.untested}</b> not replayed yet</li>
      </ul>
      <p class="small">Answer so far: <b>mostly yes, at brain level.</b> Only experiments where the brain decides by itself are counted:
        we nudge eye or sense neurons, not the command neurons. ${sc.pipeline_checks.length} more published experiments nudge the command neurons directly;
        those only check our own code, so they are listed separately below and not counted.</p>
      ${brainBreakdown(sc)}
    </div>
  </section>`;
}

const VERB = { agrees: ['good', 'same as real flies'], depends: ['mid', 'same only with strong stimulation'], disagrees: ['bad', 'different from real flies'],
  unclear: ['none', 'no clear answer'], untested: ['none', 'not replayed yet'] };

function brainLine(x) {
  const act = x.manipulation === 'silence' ? 'switching off' : 'switching on';
  const what = x.effect === 'reduce' ? `they ${DOES[x.behavior].replace(/^start /, '')} less` : `they ${DOES[x.behavior]}`;
  const ro = x.readout_plain || 'the matching command neurons';
  const [cls, txt] = VERB[x.verdict];
  const said = { agrees: x.effect === 'reduce' ? `the ${ro} were held back, as in real flies` : `the ${ro} switched on, as in real flies`,
    depends: `the ${ro} switched on with strong stimulation (150 pulses/s) but stayed off with gentle stimulation (10–75 pulses/s)`,
    disagrees: `the ${ro} stayed off, unlike in real flies`, unclear: 'the runs so far did not test this directly', untested: 'not replayed yet' }[x.verdict];
  const name = `${x.target_plain}${x.target_plain.includes(x.target) || x.target_plain.includes('(') ? '' : ` (${x.target})`}`;
  return `<li class="${cls}"><div class="real"><b>Real flies</b> <span class="small-inline">(${esc(x.citation.first_author)} et al. ${esc(x.citation.year)},
      <a href="https://doi.org/${esc(x.citation.doi)}" target="_blank" rel="noopener">paper</a>)</span>: ${esc(act)} the ${esc(name)} → ${esc(what)}.</div>
    <div class="ours"><b>Brain copy:</b> <span class="res ${cls}"><span class="dot ${cls}"></span>${esc(txt)}</span> <span class="small-inline">${esc(said)}</span></div></li>`;
}

function brainBreakdown(sc) {
  const order = { disagrees: 0, depends: 1, agrees: 2, unclear: 3, untested: 4 };
  const items = sc.items.slice().sort((a, c) => order[a.verdict] - order[c.verdict]);
  return `<details class="s-row mid" open><summary><b>Every published experiment we compare against</b>
      <span class="cnt">${sc.n_total - sc.counts.untested} of ${sc.n_total} replayed</span></summary>
      <ul class="imps">${items.map(brainLine).join('')}</ul></details>
    <details class="s-row none"><summary><b>Not counted: checks of our own code</b><span class="cnt">${sc.pipeline_checks.length} experiments</span></summary>
      <p class="why">These experiments switch on the command neurons themselves (for example the escape neuron or the moonwalker neurons).
        Our brain-to-body link turns exactly these neurons into movement, so the result is guaranteed by our code. They show the pipeline works, nothing more.</p>
      <ul class="imps">${sc.pipeline_checks.map((x) => `<li>${esc(x.manipulation === 'silence' ? 'Switching off' : 'Switching on')} the ${esc(x.target_plain)}
        → ${esc(DOES[x.behavior] || x.behavior)} <span class="small-inline">(${esc(x.citation.first_author)} et al. ${esc(x.citation.year)})</span></li>`).join('')}</ul></details>`;
}

function videos(b) {
  const m = b.media || [];
  if (!m.length) return '';
  const card = (x) => {
    const thr = x.threshold_hz ? ` · take-off rule: ${fmt(x.threshold_hz)} or more` : '';
    return `<figure class="s-vid">
      <video src="${esc(x.video)}" muted loop playsinline autoplay preload="metadata" aria-label="Simulation video: ${esc(x.nudge)}"></video>
      <figcaption><b>Nudge:</b> ${esc(x.nudge)}<br>
        <b>Brain copy:</b> ${esc(x.group_plain)} fired <b>${fmt(x.rate_hz, 1)}</b> signals per second${esc(thr)}<br>
        <b>Body:</b> ${esc(String(x.body).replace(/_/g, ' '))}
        <span class="chip ${x.kind === 'built in' ? 'none' : 'mid'}">${x.kind === 'built in' ? 'built into our code' : 'brain decided, body illustrates'}</span></figcaption></figure>`;
  };
  return `<section><h3>Watch the virtual fly</h3>
    <p class="small">These are real physics simulations computed from the brain copy's output. They show the brain's decision as a movement.
      The brain decides how strongly the command neuron fires. Our hand-built rule turns that into the movement (for example: escape neuron at about 74 signals per second or more → take off).
      So the videos illustrate the brain result; the number is the evidence.</p>
    <div class="s-vids">${m.map(card).join('')}</div></section>`;
}

function vision(b) {
  return `<section class="s-visionbox"><h3>The long-term goal</h3>
    <p>${esc(String(b.hypothesis.vision || '').replace(/^Long-term goal \(unchanged\): /, ''))}</p>
    <ul>
      <li><b>Next big step:</b> simulate the fly's nerve cord (its "spinal cord") so that leg and wing movements come from real wiring instead of our rule. That is research of months, not hours.</li>
      <li><b>Strongest next control:</b> run the same nudges on a randomly rewired brain. If the agreement with real flies drops, it is the specific wiring that matters.</li>
      <li><b>Real flies:</b> test the model's new predictions in a fly lab, for example LC17 triggering the escape neuron.</li>
    </ul></section>`;
}

const DOES = { forward: 'walk forward', backward: 'back away', turn_left: 'turn left', turn_right: 'turn right',
  escape: 'jump away (take off)', flight_power: 'flap their wings harder', feed: 'start eating', groom: 'clean their antennae' };

function howItWorks() {
  const steps = [
    ['Virtual brain', 'A computer model of all 139,000 nerve cells of a fruit fly, wired exactly as measured in a real fly brain.'],
    ['Nudge neurons', 'We switch on (or off) the same nerve cells that scientists switched on in real flies, for example the cells that see a looming object.'],
    ['Read the command neurons', 'We measure which command neurons switch on, such as the escape neuron, and which stay off.'],
    ['Compare', 'Same as in the real fly? An independent checker re-runs every experiment. A physics-simulated body shows the decision as a movement.'],
  ];
  return `<section class="s-how"><h3>How it works</h3><ol>${steps.map(([t, d], i) => `<li><span class="num">${i + 1}</span><b>${esc(t)}</b><p>${esc(d)}</p></li>`).join('')}</ol></section>`;
}

function doseChart(session, b) {
  // Screens of one session at several stimulation strengths: escape-neuron activity per cell type.
  const screens = b.experiments.filter((x) => x.session === session.id && x.kind === 'screen');
  const rates = [...new Set(screens.map((x) => x.rate_hz))].filter((r) => r != null);
  if (screens.length < 2 || rates.length < 2) return '';
  const target = screens[0].targets?.[0] || 'GF';
  const types = {};
  for (const x of screens) for (const r of x.screen || []) (types[r.cell_type] ||= {})[x.rate_hz] = r.rates?.[target];
  const order = Object.keys(types).filter((t) => Object.keys(types[t]).length >= 2)
    .sort((a, c) => (Math.max(...Object.values(types[c]).map(Number)) - Math.max(...Object.values(types[a]).map(Number))));
  const sorted = rates.slice().sort((a, c) => c - a);
  const max = Math.max(1, ...order.flatMap((t) => Object.values(types[t]).map(Number)));
  return `<figure class="s-chart"><figcaption>How strongly the <b>${esc(plainName(target))}</b> fired (signals per second)
      when we nudged each eye-neuron type gently, more gently, most gently</figcaption>
    <div class="legend">${sorted.map((r, i) => `<span><i class="sw sw${i}"></i>${fmt(r)} pulses/s</span>`).join('')}
      <span><i class="thr"></i>about 74 needed for take-off</span></div>
    ${order.map((t) => `<div class="row"><span class="lbl">${esc(t)}</span><div class="bars">${sorted.map((r, i) => {
      const v = types[t][r];
      return v == null ? '<div class="bar-row"><span class="na">not tested</span></div>'
        : `<div class="bar-row"><span class="bar sw${i}" style="width:${(100 * v) / max}%"></span><span class="v">${+(+v).toFixed(1)}</span></div>`;
    }).join('')}<span class="thr-line" style="left:${(100 * 74) / max}%"></span></div></div>`).join('')}
  </figure>`;
}

function autoStory(s, b) {
  // Sessions without a written summary (e.g. a live one): build the story from the record itself.
  const exps = b.experiments.filter((x) => x.session === s.id);
  const lines = exps.slice(0, 8).map((x) => {
    const what = x.kind === 'screen' ? `${x.excite.length} eye-neuron types` : x.excite.map(plainName).join(' + ');
    const off = x.silence.length ? `, with ${x.silence.map(plainName).join(', ')} switched off` : '';
    const out = x.kind === 'screen'
      ? `${Object.values(x.hits_by_target || {})[0]?.length ?? 0} made the ${esc(plainName(x.targets?.[0] || ''))} fire`
      : (x.body ? `the virtual fly: ${esc(String(x.body.behavior).replace(/_/g, ' '))}` : Object.entries(x.readout_hz || {}).slice(0, 2).map(([g, v]) => `${esc(plainName(g))} ${fmt(v)}/s`).join(', ') || 'no response');
    return `Nudged ${esc(what)}${esc(off)}: ${out}.`;
  });
  return { question: s.question, knew_before: s.earlier_results_cited.length ? `The experts started from ${s.earlier_results_cited.length} results of earlier sessions.` : '',
    tried: '', found: lines, verdict: 'open', verdict_text: s.status === 'running' ? 'The experts are still working on this.' : 'See the expert details for the verdicts.', next: '' };
}

function audit(s) {
  const a = s.audit;
  if (!a) return `<div class="s-audit none"><b>Independent check:</b> not run yet for this session.</div>`;
  const { pass = 0, warn = 0, fail = 0 } = a.summary;
  const total = pass + warn + fail;
  const cls = fail ? 'bad' : warn ? 'mid' : 'good';
  const head = fail ? `${fail} of ${total} checks failed` : warn ? `${pass} of ${total} checks passed, ${warn} with a warning` : `All ${total} checks passed`;
  return `<details class="s-audit ${cls}"><summary><span class="big-mark ${cls}">${fail ? '✗' : warn ? '!' : '✓'}</span>
      <span><b>Was it done correctly? ${esc(head)}.</b><br><span class="small">An independent program re-ran every experiment and checked the experts' work${a.stale ? ' (the session has new events since this check)' : ''}. Click for details.</span></span></summary>
    <ul class="checks">${a.checks.map((c) => `<li><span class="mark ${MARK[c.status][0]}">${MARK[c.status][1]}</span><div><b>${esc(c.title)}</b><span class="small">${esc(c.detail)}</span></div></li>`).join('')}</ul>
    <div class="pd"><div><b>This proves</b><ul>${(a.proves || []).map((x) => `<li>${esc(x)}</li>`).join('')}</ul></div>
      <div><b>This does not prove</b><ul>${(a.does_not_prove || []).map((x) => `<li>${esc(x)}</li>`).join('')}</ul></div></div>
    <p class="small">Run it yourself: <code>${esc(a.reproduce)}</code> · checked ${esc(String(a.audited_at).slice(0, 16).replace('T', ' '))} UTC</p>
  </details>`;
}

function story(s, b, idx) {
  const p = s.plain || autoStory(s, b);
  const v = VERDICT[p.verdict] || VERDICT.open;
  const live = s.status === 'running' ? '<span class="chip live">● live now</span>' : '';
  return `<article class="s-story" id="story-${esc(s.id)}">
    <header><span class="step-n">Experiment ${idx + 1}</span>${live}<h4>${esc(p.title || p.question)}</h4></header>
    <div class="grid">
      <div><p class="label">The question</p><p>${esc(p.question)}</p></div>
      ${p.knew_before ? `<div><p class="label">What we knew before</p><p>${esc(p.knew_before)}</p></div>` : ''}
      ${p.tried ? `<div><p class="label">What the experts tried</p><p>${esc(p.tried)}</p></div>` : ''}
    </div>
    <p class="label">What happened</p>
    <ul class="found">${(p.found || []).map((x) => `<li>${esc(x)}</li>`).join('')}</ul>
    ${doseChart(s, b)}
    <div class="s-verdict">${verdictChip(v)} <span>${esc(p.verdict_text)}</span></div>
    ${p.next ? `<p class="next"><b>What the experts decided to do next:</b> ${esc(p.next)}</p>` : ''}
    ${p.review_note ? `<p class="s-review"><b>Reviewer note:</b> ${esc(p.review_note)}</p>` : ''}
    ${audit(s)}
    <p class="small"><a href="#" data-expert="${esc(s.id)}">See the full expert discussion for this experiment →</a>
      ${s.plain ? ' · Plain-language summary written from the lab notebook; every number is in the raw results.' : ''}</p>
  </article>`;
}

function glossaryBox() {
  const words = [
    ['Neuron (nerve cell)', 'A cell that passes on electrical signals. A fruit fly has about 139,000 in its brain.'],
    ['Signals per second', 'How busy a neuron is: how many electrical pulses it fires each second.'],
    ['Nudging / switching on', 'Feeding a group of neurons extra pulses, like scientists do with light in real flies (optogenetics).'],
    ['Switching off (silencing)', 'Making a group of neurons unable to fire, to test whether they are needed.'],
    ['Escape neuron (giant fiber)', 'A very large neuron that makes the fly jump away from danger.'],
    ['Eye neurons (LC, LPLC types)', 'Neurons behind the eye that detect specific things, for example an object coming closer.'],
  ];
  return `<section><h3>Words used on this page</h3><dl class="s-gloss">${words.map(([w, d]) => `<div><dt>${esc(w)}</dt><dd>${esc(d)}</dd></div>`).join('')}</dl></section>`;
}

export function renderSimple(b, el, onExpert) {
  glossary = b.glossary || {};
  const sessions = b.sessions.slice().reverse(); // newest first
  el.innerHTML = `${hero(b)}${videos(b)}${howItWorks()}
    <section><h3>The experiments, newest first</h3>
      <p class="small">Each experiment builds on the one before: the experts read the earlier results before planning the next test.</p>
      ${sessions.map((s) => story(s, b, b.sessions.indexOf(s))).join('')}
    </section>
    ${vision(b)}${glossaryBox()}`;
  el.querySelectorAll('[data-expert]').forEach((a) => a.addEventListener('click', (ev) => { ev.preventDefault(); onExpert(a.dataset.expert); }));
}
