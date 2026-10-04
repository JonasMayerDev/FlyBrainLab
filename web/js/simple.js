// Simple view of the expert board for non-experts: what we asked, how it works, what we found,
// and whether each experiment was done correctly (independent audit, flylab/audit.py).

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmt = (x, d = 0) => (x === null || x === undefined || Number.isNaN(+x) ? '–' : (+x).toFixed(d));

const STATUS = {
  reproduced_body: ['good', 'Matches real flies', 'The virtual fly did what real flies do, and the movement was double-checked.'],
  reproduced_brain: ['mid', 'Matches inside the brain only', 'The virtual brain reacts like a real fly\'s, but the body movement is not proven yet.'],
  conflict: ['bad', 'Does not match yet', 'At least one result disagrees with what real flies do.'],
  untested: ['none', 'Not tested yet', 'No experiment from real-fly research has been replayed for this yet.'],
};
const VERDICT = {
  yes: ['good', 'Matches real flies'], brain: ['mid', 'Matches inside the brain'], partly: ['mid', 'Partly matches'],
  no: ['bad', 'Does not match'], open: ['none', 'Open'],
};
const MARK = { pass: ['good', '✓'], warn: ['mid', '!'], fail: ['bad', '✗'], 'n/a': ['none', '–'] };

let glossary = {};
const plainName = (g) => glossary[g] || glossary[String(g).replace(/_[LR]$/, '')] || (/^L[CT]|^LPLC|^MTe|^aMe/.test(g) ? `eye neurons (type ${g})` : g);

function verdictChip([cls, text]) { return `<span class="chip ${cls}">${esc(text)}</span>`; }

function hero(b) {
  const c = b.coverage.counts;
  const n = b.coverage.behaviors.length;
  const items = [['good', c.reproduced_body || 0, 'match real flies fully'], ['mid', c.reproduced_brain || 0, 'match inside the brain only'],
    ['bad', c.conflict || 0, 'do not match yet'], ['none', c.untested || 0, 'not tested yet']];
  return `<section class="s-hero">
    <p class="kicker">Our question</p>
    <h2>Can a computer copy of a fruit fly's brain behave like a real fly?</h2>
    <p class="lead">Scientists have mapped every one of the 139,000 nerve cells in a fruit fly's brain and how they connect.
      We run that wiring as a computer model, give it the same nudges that scientists gave real flies in published experiments,
      and check whether our virtual fly reacts the way the real flies did. A board of AI experts plans each experiment, looks at the result and decides what to test next.</p>
    <div class="s-answer"><b>Answer so far:</b> partly. Of ${n} fly behaviours we can test:
      <ul class="s-tally">${items.map(([cls, k, t]) => `<li><span class="dot ${cls}"></span><b>${k}</b> ${esc(t)}</li>`).join('')}</ul>
      ${breakdown(b.coverage)}
      <details class="s-match"><summary>What does "match" mean?</summary>
        <p>We take a published experiment on real flies and replay it in the computer. <i>Example:</i> scientists switched on
          the LPLC2 neurons of real flies and the flies jumped away. We switch on the same neurons in the virtual brain and look at what happens.
          It <b>matches</b> when the virtual fly shows the same result as the real flies.</p>
        <ul>
          <li><span class="dot good"></span><b>Match real flies fully:</b> the virtual body really does it, an independent checker confirms the movement
            from the video, and the result does not just follow from how we built the model.</li>
          <li><span class="dot mid"></span><b>Match inside the brain only:</b> the virtual brain reacts the right way (for example the escape neuron fires),
            but the body was not run, its movement follows from the brain-to-body link we designed from the same papers, or the checker was unsure.</li>
          <li><span class="dot bad"></span><b>Do not match yet:</b> the virtual fly does something different from the real flies.
            Example: switching on LPLC2 makes real flies back away, but not our virtual fly.</li>
        </ul>
        <p class="small">A behaviour counts as matching when at least one replayed experiment agreed and none disagreed.
          Not every published experiment has been replayed yet; each behaviour card below shows how many were.</p>
      </details>
    </div>
  </section>`;
}

const DOES = { forward: 'walk forward', backward: 'back away', turn_left: 'turn left', turn_right: 'turn right',
  escape: 'jump away (take off)', flight_power: 'flap their wings harder', feed: 'start eating', groom: 'clean their antennae' };
const WHERE = { 'brain read-out': 'in the brain', 'walking body': 'in the walking body', 'flight body': 'in the flying body' };
const SAID = { consistent: ['good', 'same as real flies'], inconsistent: ['bad', 'different from real flies'],
  partially_consistent: ['mid', 'partly the same'], inconclusive: ['none', 'no clear answer'] };

function impulseLine(i, beh) {
  const act = i.manipulation === 'silence' ? 'switching off' : 'switching on';
  const what = i.effect === 'reduce' ? `they ${DOES[beh].replace(/^start /, '')} less` : `they ${DOES[beh]}`;
  // group identical outcomes: "same as real flies, in the brain (x2)"
  const groups = {};
  for (const t of i.tests) {
    const k = `${t.verdict}|${t.label_source}|${t.circular}|${t.verifier && !['correct'].includes(t.verifier) ? 'unsure' : ''}`;
    (groups[k] ||= { t, n: 0 }).n += 1;
  }
  const res = Object.values(groups).map(({ t, n }) => {
    const [cls, txt] = SAID[t.verdict] || SAID.inconclusive;
    const notes = [t.circular ? 'built into our brain-to-body link' : '', t.verifier && t.verifier !== 'correct' ? 'checker unsure' : ''].filter(Boolean);
    return `<span class="res ${cls}"><span class="dot ${cls}"></span>${esc(txt)} ${esc(WHERE[t.label_source] || '')}${n > 1 ? ` (${n}×)` : ''}${notes.length ? ` <i>(${esc(notes.join(', '))})</i>` : ''}</span>`;
  }).join('');
  return `<li><div class="real"><b>Real flies</b> <span class="small-inline">(${esc(i.citation.first_author)} et al. ${esc(i.citation.year)},
      <a href="https://doi.org/${esc(i.citation.doi)}" target="_blank" rel="noopener">paper</a>)</span>: ${esc(act)} the ${esc(plainName(i.target))}${plainName(i.target).includes(i.target) || plainName(i.target).includes('(') ? '' : ` (${esc(i.target)})`} → ${esc(what)}.</div>
    <div class="ours"><b>Our virtual fly:</b> ${res || '<span class="res none"><span class="dot none"></span>not replayed yet</span>'}</div></li>`;
}

function whyNot(b) {
  if (b.status === 'reproduced_body') return '';
  const ok = b.impulses.flatMap((i) => i.tests).filter((t) => t.verdict === 'consistent');
  const bad = b.impulses.filter((i) => i.tests.some((t) => t.verdict === 'inconsistent'));
  const reasons = [];
  if (bad.length) reasons.push(`when we switched on ${bad.map((i) => i.target).join(' or ')}, the virtual fly did something different from the real flies`);
  if (ok.some((t) => t.label_source === 'brain read-out')) reasons.push('some results were only measured in the brain, not as a body movement');
  if (ok.some((t) => t.circular)) reasons.push('the body movement comes from the brain-to-body link we built from the same papers, so it cannot count as independent');
  if (ok.some((t) => t.verifier && t.verifier !== 'correct')) reasons.push('the movement checker could not confirm the video');
  const open = b.impulses.filter((i) => !i.tests.length).length;
  if (open) reasons.push(`${open} of ${b.n_impulses} published experiments have not been replayed yet`);
  return reasons.length ? `<div class="why"><b>${b.status === 'conflict' ? 'Why it does not match:' : 'Why not "fully":'}</b>
    <ul>${reasons.map((r) => `<li>${esc(r[0].toUpperCase() + r.slice(1))}.</li>`).join('')}</ul></div>` : '';
}

function breakdown(cov) {
  const order = { conflict: 0, reproduced_body: 1, reproduced_brain: 2, untested: 3 };
  const rows = cov.behaviors.slice().sort((a, c) => order[a.status] - order[c.status]).map((b) => {
    const [cls, label] = STATUS[b.status];
    return `<details class="s-row ${cls}"><summary><span class="dot ${cls}"></span><b>${esc(b.plain || b.label)}</b>
        <span class="chip ${cls}">${esc(label)}</span><span class="cnt">${b.n_tested} of ${b.n_impulses} real-fly experiments replayed</span></summary>
      ${whyNot(b)}
      <ul class="imps">${b.impulses.map((i) => impulseLine(i, b.id)).join('')}</ul></details>`;
  }).join('');
  const total = cov.n_impulses, done = cov.n_impulses_tested;
  return `<p class="s-sub">Behaviour by behaviour (click one to see every experiment):</p>
    <div class="s-rows">${rows}</div>
    <div class="s-need"><b>What is still missing for a full "yes"</b><ul>
      <li>A body movement that the brain decides on by itself (we nudge eye or sense neurons, not the neurons our brain-to-body link reads) and that the movement checker confirms.
        Closest so far: eye neurons LPLC2 → take-off. The video exists, but the checker could not confirm it because the camera follows the fly, so the height gain is hard to see.
        Even then, how the legs and wings move comes from our hand-built link: the fly's nerve cord (its "spinal cord") is not simulated.</li>
      <li>Replaying the remaining ${total - done} of ${total} published experiments (${done} done so far).</li>
      <li>Behaviours we have no published experiment for yet: ${cov.not_catalogued.map(esc).join(', ')}.</li>
      <li>Testing the model's new predictions in real flies, for example LC17 triggering escape.</li>
    </ul></div>`;
}

function howItWorks() {
  const steps = [
    ['Virtual brain', 'A computer model of all 139,000 nerve cells of a fruit fly, wired exactly as measured in a real fly brain.'],
    ['Nudge neurons', 'We switch on (or off) the same nerve cells that scientists switched on in real flies, for example the cells that see a looming object.'],
    ['Virtual body', 'The brain\'s output drives a physics-simulated fly that can walk and fly.'],
    ['Compare', 'Did the virtual fly do what the real flies did in the published experiment? An independent checker re-runs everything.'],
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
  el.innerHTML = `${hero(b)}${howItWorks()}
    <section><h3>The experiments, newest first</h3>
      <p class="small">Each experiment builds on the one before: the experts read the earlier results before planning the next test.</p>
      ${sessions.map((s) => story(s, b, b.sessions.indexOf(s))).join('')}
    </section>
    ${glossaryBox()}`;
  el.querySelectorAll('[data-expert]').forEach((a) => a.addEventListener('click', (ev) => { ev.preventDefault(); onExpert(a.dataset.expert); }));
}
