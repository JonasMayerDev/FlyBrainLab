// Cinematic film of the Embodied Fly Lab (web/film.html). Deterministic: renderAt(t) draws frame t (seconds),
// so tools/render_film.py can capture it frame by frame. All body motion = recorded simulation poses,
// all lit neurons = recorded brain-model activity. The sugar cube is an illustrative prop (labelled on screen).
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

const UNIT = { mm: 1, cm: 10, m: 1000, model: 1 };
const DURATION = 59.5;
const CAPTURE = new URLSearchParams(location.search).has('capture');

// ---------- helpers ----------
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const smooth = (x) => { x = clamp(x); return x * x * (3 - 2 * x); };
const ramp = (t, a, b) => smooth((t - a) / (b - a));
const win = (t, a, b, f = 0.6) => Math.min(ramp(t, a, a + f), 1 - ramp(t, b - f, b));
const lerp = (a, b, x) => a + (b - a) * x;
const V = (x, y, z) => new THREE.Vector3(x, y, z);
async function json(u) { const r = await fetch(u); if (!r.ok) throw new Error(u); return r.json(); }

// ---------- renderer ----------
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(CAPTURE ? 1 : Math.min(2, window.devicePixelRatio || 1));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
document.body.prepend(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000000);
scene.fog = new THREE.FogExp2(0x000000, 0.0045);
const camera = new THREE.PerspectiveCamera(32, window.innerWidth / window.innerHeight, 0.01, 4000);
scene.add(new THREE.AmbientLight(0x8899bb, 0.6));
const key = new THREE.DirectionalLight(0xffffff, 2.2); key.position.set(40, 80, 60); scene.add(key);
const rim = new THREE.DirectionalLight(0x88aaff, 1.4); rim.position.set(-60, 30, -80); scene.add(rim);
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 0.7, 0.5, 0.42);
composer.addPass(bloom);
composer.addPass(new OutputPass());
window.addEventListener('resize', () => {
  renderer.setSize(window.innerWidth, window.innerHeight); composer.setSize(window.innerWidth, window.innerHeight);
  camera.aspect = window.innerWidth / window.innerHeight; camera.updateProjectionMatrix();
});

// MuJoCo world (z up, mm) inside three (y up)
const world = new THREE.Group(); world.rotation.x = -Math.PI / 2; scene.add(world);

// floor: soft radial disc
function radialTexture(inner, outer) {
  const c = document.createElement('canvas'); c.width = c.height = 512;
  const g = c.getContext('2d'); const gr = g.createRadialGradient(256, 256, 0, 256, 256, 256);
  gr.addColorStop(0, inner); gr.addColorStop(1, outer); g.fillStyle = gr; g.fillRect(0, 0, 512, 512);
  return new THREE.CanvasTexture(c);
}
const floor = new THREE.Mesh(new THREE.CircleGeometry(16, 96),
  new THREE.MeshBasicMaterial({ map: radialTexture('rgba(34,40,56,0.55)', 'rgba(0,0,0,0)'), transparent: true, depthWrite: false }));
world.add(floor);
const ring = new THREE.Mesh(new THREE.RingGeometry(5.5, 5.62, 128), new THREE.MeshBasicMaterial({ color: 0x3a4766, transparent: true, opacity: 0.25 }));
ring.position.z = 0.01; world.add(ring);

// ---------- glass fly ----------
const glassVS = `varying vec3 vN; varying vec3 vV;
  void main(){ vec4 mv = modelViewMatrix * vec4(position,1.0); vN = normalize(normalMatrix * normal); vV = normalize(-mv.xyz); gl_Position = projectionMatrix * mv; }`;
const glassFS = `uniform vec3 uBase; uniform vec3 uRim; uniform float uAlpha; varying vec3 vN; varying vec3 vV;
  void main(){ float ln = length(vN); vec3 n = ln > 1e-6 ? vN / ln : vec3(0.0, 0.0, 1.0); float lv = length(vV); vec3 v = lv > 1e-6 ? vV / lv : vec3(0.0, 0.0, 1.0); float f = pow(clamp(1.0 - abs(dot(n, v)), 0.0, 1.0), 2.2);
    gl_FragColor = vec4(mix(uBase, uRim, f), uAlpha * (0.03 + 0.55 * f)); }`;
function glassMat(base, rimC) {
  return new THREE.ShaderMaterial({ uniforms: { uBase: { value: new THREE.Color(base) }, uRim: { value: new THREE.Color(rimC) }, uAlpha: { value: 1 } },
    vertexShader: glassVS, fragmentShader: glassFS, transparent: true, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending });
}

async function loadGeom(url) {
  const meta = await json(url);
  const buf = await (await fetch(url.replace(/[^/]+$/, meta.bin))).arrayBuffer();
  const verts = new Float32Array(buf, 0, meta.vertex_floats);
  const idx = meta.index_type === 'uint32' ? new Uint32Array(buf, meta.index_byte_offset, meta.index_count)
    : new Uint16Array(buf, meta.index_byte_offset, meta.index_count);
  return { meta, verts, idx };
}
function primitive(g) {
  const s = g.size; let geo;
  if (g.type === 'sphere') geo = new THREE.SphereGeometry(s[0], 16, 12);
  else if (g.type === 'ellipsoid') { geo = new THREE.SphereGeometry(1, 16, 12); geo.scale(s[0], s[1], s[2]); }
  else if (g.type === 'capsule') { geo = new THREE.CapsuleGeometry(s[0], 2 * s[1], 4, 12); geo.rotateX(Math.PI / 2); }
  else if (g.type === 'cylinder') { geo = new THREE.CylinderGeometry(s[0], s[0], 2 * s[1], 16); geo.rotateX(Math.PI / 2); }
  else if (g.type === 'box') geo = new THREE.BoxGeometry(2 * s[0], 2 * s[1], 2 * s[2]);
  return geo || null;
}
function buildFly(geom) {
  const root = new THREE.Group(); root.scale.setScalar(UNIT[geom.meta.units] ?? 1); world.add(root);
  const bodies = new Map();
  const body = glassMat(0x1b2740, 0xcfe0ff), wing = glassMat(0x0d1424, 0x9fb8ff), eye = glassMat(0x2a0c0c, 0xff8a7a);
  for (const g of geom.meta.geoms) {
    let bg = bodies.get(g.body);
    if (!bg) { bg = new THREE.Group(); bg.name = g.body; bodies.set(g.body, bg); root.add(bg); }
    let geo;
    if (g.type === 'mesh' && g.mesh) {
      geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(geom.verts.subarray(g.mesh.vOff, g.mesh.vOff + 3 * g.mesh.vCount), 3));
      geo.setIndex(new THREE.BufferAttribute(geom.idx.subarray(g.mesh.iOff, g.mesh.iOff + g.mesh.iCount), 1));
      geo.computeVertexNormals();
    } else geo = primitive(g);
    if (!geo) continue;
    const n = (g.body + ' ' + (g.name || '')).toLowerCase();
    const m = new THREE.Mesh(geo, /wing/.test(n) ? wing : /eye/.test(n) ? eye : body);
    m.position.fromArray(g.pos); m.quaternion.set(g.quat[1], g.quat[2], g.quat[3], g.quat[0]); m.updateMatrix();
    bg.add(m);
  }
  return { root, bodies, mats: [body, wing, eye], unit: UNIT[geom.meta.units] ?? 1 };
}
function setAlpha(fly, a) { fly.mats.forEach((m, i) => { m.uniforms.uAlpha.value = a * (i === 1 ? 0.55 : 1); }); fly.root.visible = a > 0.002; }

// pose access (MuJoCo frame, mm)
function frameAt(P, t) {
  const T = P.t, n = T.length; let f = 0;
  while (f < n - 1 && T[f + 1] <= t) f++;
  const f1 = Math.min(n - 1, f + 1);
  const a = f1 === f ? 0 : clamp((t - T[f]) / (T[f1] - T[f]));
  return { f, f1, a };
}
const _q0 = new THREE.Quaternion(), _q1 = new THREE.Quaternion();
function applyPose(fly, P, t) {
  const { f, f1, a } = frameAt(P, t);
  const p0 = P.p[f], p1 = P.p[f1], q0 = P.q[f], q1 = P.q[f1];
  P.bodies.forEach((name, i) => {
    const g = fly.bodies.get(name); if (!g) return;
    const j = 3 * i, k = 4 * i;
    g.position.set(lerp(p0[j], p1[j], a), lerp(p0[j + 1], p1[j + 1], a), lerp(p0[j + 2], p1[j + 2], a));
    _q0.set(q0[k + 1], q0[k + 2], q0[k + 3], q0[k]); _q1.set(q1[k + 1], q1[k + 2], q1[k + 3], q1[k]);
    g.quaternion.slerpQuaternions(_q0, _q1, a);
  });
  for (const [name, g] of fly.bodies) g.visible = P.bodies.includes(name);
}
function bodyPose(P, name, t, u) {
  const i = P.bodies.indexOf(name); if (i < 0) return null;
  const { f, f1, a } = frameAt(P, t), j = 3 * i, k = 4 * i;
  const p = V(lerp(P.p[f][j], P.p[f1][j], a), lerp(P.p[f][j + 1], P.p[f1][j + 1], a), lerp(P.p[f][j + 2], P.p[f1][j + 2], a)).multiplyScalar(u);
  const q0 = new THREE.Quaternion(P.q[f][k + 1], P.q[f][k + 2], P.q[f][k + 3], P.q[f][k]);
  const q1 = new THREE.Quaternion(P.q[f1][k + 1], P.q[f1][k + 2], P.q[f1][k + 3], P.q[f1][k]);
  return { p, q: q0.slerp(q1, a) };
}

// ---------- brain ----------
const CLASS_COL = { central: 0x8fb3ff, optic: 0x2f4a8a, visual_projection: 0x6fd3ff, visual_centrifugal: 0x4f7bd0, sensory: 0x7af0c2,
  ascending: 0xb59cff, descending: 0xffd27a, motor: 0xff8a65, endocrine: 0xff9ad5, unknown: 0x8890a8 };
const brain = { group: new THREE.Group(), base: null, act: null, local: null, n: 0, width: 815 };
world.add(brain.group);
async function loadBrain() {
  const meta = await json('data/brain_points.json');
  const buf = await (await fetch('data/' + meta.bin)).arrayBuffer();
  const n = meta.n, raw = new Float32Array(buf, 0, 3 * n), cls = new Uint8Array(buf, 12 * n, n);
  const [cx, cy, cz] = meta.center;
  brain.local = new Float32Array(3 * n);
  const pos = [], col = [];
  const pal = meta.classes.map((c) => new THREE.Color(CLASS_COL[c] ?? 0x8890a8));
  for (let i = 0; i < n; i++) {
    const x = raw[3 * i], y = raw[3 * i + 1], z = raw[3 * i + 2];
    // FlyWire (x: left->right, y: ventral+, z: posterior+, um) -> head-local MuJoCo frame (x fwd, y left, z up), um
    const X = -(z - cz), Y = -(x - cx), Z = -(y - cy);
    brain.local[3 * i] = X; brain.local[3 * i + 1] = Y; brain.local[3 * i + 2] = Z;
    if (!Number.isFinite(x)) continue;
    pos.push(X, Y, Z); const c = pal[cls[i]] || pal[pal.length - 1]; const k = cls[i] === 1 ? 0.35 : 0.8; col.push(c.r * k, c.g * k, c.b * k);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  brain.base = new THREE.Points(geo, new THREE.PointsMaterial({ size: 0.0035, sizeAttenuation: true, vertexColors: true, transparent: true,
    opacity: 0.3, depthWrite: false, blending: THREE.AdditiveBlending }));
  brain.group.add(brain.base);
  brain.n = n; brain.width = meta.bbox_max[0] - meta.bbox_min[0];
}
const activeSets = {};
function makeActive(run, color) {
  const b = run.brain, idx = b.active_idx || [], rate = b.active_rate_hz || [];
  const pos = [], col = [], c = new THREE.Color(color), stim = new Set(b.stimulated_idx || []);
  idx.forEach((i, j) => {
    const X = brain.local[3 * i]; if (!Number.isFinite(X)) return;
    pos.push(X, brain.local[3 * i + 1], brain.local[3 * i + 2]);
    const k = stim.has(i) ? 1.6 : 0.45 + 0.9 * clamp(rate[j] / 150);
    col.push(c.r * k, c.g * k, c.b * k);
  });
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  const pts = new THREE.Points(geo, new THREE.PointsMaterial({ size: 0.014, sizeAttenuation: true, vertexColors: true, transparent: true,
    opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending }));
  brain.group.add(pts);
  return pts;
}
function placeBrain(pos, quat, widthMm) {
  brain.group.position.copy(pos); brain.group.quaternion.copy(quat); brain.group.scale.setScalar(widthMm / brain.width);
}

// ---------- signal pulses (brain -> legs / wings) ----------
const PULSE_K = 42;
const pulse = { pts: null, curves: [] };
function initPulses(maxCurves = 8) {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(maxCurves * PULSE_K * 3), 3));
  geo.setAttribute('color', new THREE.BufferAttribute(new Float32Array(maxCurves * PULSE_K * 3), 3));
  pulse.pts = new THREE.Points(geo, new THREE.PointsMaterial({ size: 0.09, sizeAttenuation: true, vertexColors: true, transparent: true,
    depthWrite: false, blending: THREE.AdditiveBlending }));
  pulse.pts.frustumCulled = false; world.add(pulse.pts);
}
function drawPulses(starts, ends, color, t, alpha, speed = 0.9) {
  const P = pulse.pts.geometry.attributes.position.array, C = pulse.pts.geometry.attributes.color.array;
  P.fill(0); C.fill(0);
  const c = new THREE.Color(color), tmp = new THREE.Vector3();
  ends.forEach((e, ci) => {
    const s = starts; const mid = s.clone().add(e).multiplyScalar(0.5); mid.z -= 0.25 * s.distanceTo(e);
    const curve = new THREE.QuadraticBezierCurve3(s, mid, e);
    for (let k = 0; k < PULSE_K; k++) {
      const u = k / (PULSE_K - 1); curve.getPoint(u, tmp);
      const o = 3 * (ci * PULSE_K + k);
      P[o] = tmp.x; P[o + 1] = tmp.y; P[o + 2] = tmp.z;
      const ph = (t * speed + ci * 0.07) % 1;
      const glow = 0.18 + 1.6 * Math.exp(-((u - ph) ** 2) / 0.006);
      C[o] = c.r * glow * alpha; C[o + 1] = c.g * glow * alpha; C[o + 2] = c.b * glow * alpha;
    }
  });
  pulse.pts.geometry.attributes.position.needsUpdate = true; pulse.pts.geometry.attributes.color.needsUpdate = true;
}

// ---------- text ----------
const $ = (id) => document.getElementById(id);
const cues = [];
function cue(id, text, a, b, cls = '') { cues.push({ id, text, a, b, cls }); }
function drawText(t) {
  for (const id of ['title', 'sub', 'note']) {
    const c = cues.find((q) => q.id === id && t >= q.a && t <= q.b);
    const el = $(id);
    if (!c) { el.style.opacity = 0; continue; }
    if (el.textContent !== c.text) el.textContent = c.text;
    el.className = 't ' + c.cls;
    const o = win(t, c.a, c.b, 0.7);
    el.style.opacity = o; el.style.transform = `translateY(${(1 - o) * 14}px)`;
  }
}
// story (seconds): the real experiment - agents stimulate looming detectors, the brain model routes the
// signal to the giant-fiber escape neurons, the adapter turns that into a takeoff; control with GF silenced.
cue('title', '138,639 neurons.', 0.8, 6.4);
cue('sub', 'A complete fruit-fly brain, simulated neuron by neuron.', 1.5, 6.4);
cue('title', 'AI agents run the lab.', 7.0, 12.8);
cue('sub', 'Omnigent agents decide which neurons to stimulate, run the experiment and check the result.', 7.6, 12.8);
cue('title', 'Neurons, mapped to movement.', 13.4, 19.2);
cue('sub', 'In the simulated brain we study how the fruit fly responds to different stimuli.', 14.0, 19.2);
cue('title', 'Stimulus: a looming threat.', 19.8, 25.0);
cue('sub', 'The agents drive the looming detectors (LPLC2) in both eyes.', 20.4, 25.0);
cue('title', 'The brain processes it.', 25.4, 30.8);
cue('sub', 'Activity spreads through the network and reaches the giant-fiber escape neurons.', 26.0, 30.8);
cue('title', 'Escape.', 31.2, 38.8, 'green');
cue('sub', 'The giant fiber fires at 152–169 Hz. The virtual fly takes off.', 31.8, 38.8);
cue('title', 'Another neuron: no escape.', 39.4, 45.2);
cue('sub', 'Stimulating the moonwalker neurons (MDN) instead: the giant fiber stays silent and the fly walks backward.', 40.0, 45.2);
cue('title', 'What the agents found.', 45.8, 50.8, 'grad');
cue('sub', 'With gentler stimulation, LC17, a cell type not known from escape studies, drove the escape neuron most strongly: a prediction for the real lab.', 46.4, 50.8);
cue('title', 'Checked by an AI expert board.', 51.2, 55.4);
cue('title', 'FlyBrainLab', 55.9, 59.5, 'grad end');
cue('sub', 'Our agents tackle complex scientific problems by testing, validating through simulation and comparing with published research.', 56.3, 59.5, 'end');
cue('note', 'Recorded simulations: FlyWire v783 brain model (after Shiu et al. 2024). Lit neurons = mean firing rates of the recorded run.', 0.5, 19.2);
cue('note', 'Looming object shown symbolically: in the model the LPLC2 neurons are driven directly. Spreading wave illustrative; lit neurons = recorded mean rates. Brain shown scaled inside the head.', 19.6, 30.8);
cue('note', 'Recorded run: brain model → frozen adapter (giant fiber → takeoff) → FlyBody physics, simplified aerodynamics, slow motion.', 31.2, 39.0);
cue('note', 'Recorded run: MDN driven directly, giant fiber 0 Hz. NeuroMechFly walking body; backward stepping approximated; slow motion.', 39.4, 45.2);
cue('note', 'Session 3 of the agent lab (lower stimulus drive). Agent-generated prediction, not confirmed in a real fly.', 45.8, 50.8);
cue('note', 'Audit: 3 sessions, 25 experiments re-run with the same seeds. 8/9: 5 checks circular by design, 3 emergent, 1 disagrees. 25×: first hit of the MDN screen vs. random order (5× vs. a strong baseline).', 51.4, 55.4);
cue('note', 'FlyWire · Shiu et al. 2024 · NeuroMechFly · FlyBody · Omnigent (open source, by Databricks) · Hack-Nation 7, Challenge 03', 56.4, 59.5);

// ---------- load ----------
const S = {};
function pointsLayer(idxList, colorFn, size) {
  const pos = [], col = [], keep = [];
  idxList.forEach((i, j) => {
    const X = brain.local[3 * i]; if (!Number.isFinite(X)) return;
    pos.push(X, brain.local[3 * i + 1], brain.local[3 * i + 2]); col.push(0, 0, 0); keep.push(j);
  });
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  const pts = new THREE.Points(geo, new THREE.PointsMaterial({ size, sizeAttenuation: true, vertexColors: true, transparent: true,
    opacity: 1, depthWrite: false, blending: THREE.AdditiveBlending }));
  brain.group.add(pts);
  return { pts, keep, n: pos.length / 3, colorFn };
}
function paint(layer, fn) {
  const C = layer.pts.geometry.attributes.color.array;
  for (let k = 0; k < layer.n; k++) { const c = fn(k); C[3 * k] = c[0]; C[3 * k + 1] = c[1]; C[3 * k + 2] = c[2]; }
  layer.pts.geometry.attributes.color.needsUpdate = true;
}
function buildRunLayers(run) {
  const b = run.brain, stim = new Set(b.stimulated_idx || []), sil = new Set(b.silenced_idx || []), ro = new Set(b.readout_idx || []);
  const rate = new Map(); (b.active_idx || []).forEach((i, j) => rate.set(i, b.active_rate_hz[j]));
  const stimIdx = [...stim];
  const gfIdx = [...ro].filter((i) => !stim.has(i) && ((rate.get(i) || 0) > 50 || sil.has(i)));
  const downIdx = (b.active_idx || []).filter((i) => !stim.has(i) && !gfIdx.includes(i));
  // wave order: distance from the nearest stimulated (LPLC2) neuron cluster centre, normalised to 0..1 (illustrative)
  const P = (i) => [brain.local[3 * i], brain.local[3 * i + 1], brain.local[3 * i + 2]];
  const cents = [[0, 0, 0, 0], [0, 0, 0, 0]];
  stimIdx.forEach((i) => { const p = P(i); if (!Number.isFinite(p[0])) return; const s = p[1] > 0 ? 0 : 1; cents[s][0] += p[0]; cents[s][1] += p[1]; cents[s][2] += p[2]; cents[s][3]++; });
  const C = cents.filter((c) => c[3] > 0).map((c) => [c[0] / c[3], c[1] / c[3], c[2] / c[3]]);
  const dist = (i) => { const p = P(i); return Math.min(...C.map((c) => Math.hypot(p[0] - c[0], p[1] - c[1], p[2] - c[2]))); };
  const dd = downIdx.map(dist); const dmax = Math.max(...dd.filter(Number.isFinite), 1);
  return {
    stim: pointsLayer(stimIdx, null, 0.016),
    down: Object.assign(pointsLayer(downIdx, null, 0.012), { d: dd.map((x) => x / dmax), r: downIdx.map((i) => rate.get(i) || 0) }),
    gf: Object.assign(pointsLayer(gfIdx, null, 0.05), { silenced: gfIdx.map((i) => sil.has(i)) }),
  };
}
async function init() {
  try { await Promise.all([document.fonts.load('650 64px Inter'), document.fonts.load('700 96px Inter'), document.fonts.load('400 32px Inter'), document.fonts.load('500 20px Inter')]); await document.fonts.ready; } catch (e) { /* system font */ }
  const [gFB, gNMF, rTake, rMdn] = await Promise.all([
    loadGeom('data/geometry/flybody.json'), loadGeom('data/geometry/neuromechfly.json'), json('data/runs/lplc2_takeoff.json'), json('data/runs/mdn_backward.json'), loadBrain()]);
  S.fb = buildFly(gFB); S.nmf = buildFly(gNMF);
  S.take = rTake.body.poses; S.mdn = rMdn.body.poses; S.u = UNIT[S.take.units] ?? 1; S.uW = UNIT[S.mdn.units] ?? 1;
  S.L = buildRunLayers(rTake); S.LS = buildRunLayers(rMdn);
  const hb = new THREE.Box3(); const head = S.fb.bodies.get('head');
  head.children.forEach((m) => { m.geometry.computeBoundingBox(); hb.union(m.geometry.boundingBox.clone().applyMatrix4(m.matrix)); });
  S.headOff = hb.getCenter(new THREE.Vector3()).multiplyScalar(S.fb.unit);
  const hs = hb.getSize(new THREE.Vector3()); S.headW = Math.max(hs.x, hs.y, hs.z) * S.fb.unit;
  initPulses(8);
  S.trail = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: 0x6ff0ac, transparent: true, opacity: 0.5, blending: THREE.AdditiveBlending }));
  const ti = S.take.bodies.indexOf('thorax'); const tp = [];
  S.take.p.forEach((p) => tp.push(p[3 * ti] * S.u, p[3 * ti + 1] * S.u, p[3 * ti + 2] * S.u));
  S.trail.geometry.setAttribute('position', new THREE.Float32BufferAttribute(tp, 3)); S.trail.frustumCulled = false; world.add(S.trail);
  // symbolic looming object (dark sphere with a red rim) approaching the fly's eye
  S.loom = new THREE.Mesh(new THREE.SphereGeometry(1, 48, 32), glassMat(0x0a0303, 0xff5a4f)); world.add(S.loom);
}

// ---------- frame ----------
function camOrbit(target, r, azDeg, elDeg) {
  const az = THREE.MathUtils.degToRad(azDeg), el = THREE.MathUtils.degToRad(elDeg);
  const m = V(target.x + r * Math.cos(el) * Math.cos(az), target.y + r * Math.cos(el) * Math.sin(az), target.z + r * Math.sin(el));
  const toThree = (v) => V(v.x, v.z, -v.y);
  camera.position.copy(toThree(m)); camera.lookAt(toThree(target));
}
const WINGS_LEGS = ['wing_left', 'wing_right', 'coxa_T2_left', 'coxa_T2_right'];

function renderAt(t) {
  t = clamp(t, 0, DURATION);
  const control = t >= 39.2 && t < 45.6;
  const P = control ? S.mdn : S.take;
  const simT = control ? clamp((t - 40.4) * 0.2, 0, 0.99) : (t < 32.2 ? 0 : clamp((t - 32.2) / 6.2 * 0.99, 0, 0.99));
  // body: hidden while the brain is the subject; appears for the escape and the comparison run
  const bodyA = t < 30.6 ? 0.0 : (t < 45.6 ? ramp(t, 30.6, 32.0) : 1 - ramp(t, 45.6, 46.6));
  setAlpha(S.fb, control ? 0 : bodyA);
  setAlpha(S.nmf, control ? 1 : 0);
  let thorax;
  if (control) {
    applyPose(S.nmf, P, simT);
    const l = bodyPose(P, 'nmf/l_eye', simT, S.uW), r = bodyPose(P, 'nmf/r_eye', simT, S.uW), tq = bodyPose(P, 'nmf/c_thorax', simT, S.uW);
    placeBrain(l.p.clone().add(r.p).multiplyScalar(0.5), tq.q, 0.8 * l.p.distanceTo(r.p));
    thorax = tq.p;
  } else {
    applyPose(S.fb, P, simT);
    const h = bodyPose(P, 'head', simT, S.u), th = bodyPose(P, 'thorax', simT, S.u);
    placeBrain(h.p.clone().add(S.headOff.clone().applyQuaternion(h.q)), th.q, 0.72 * S.headW);
    thorax = th.p;
  }
  const bc = brain.group.position.clone();

  // ---- brain layers
  brain.base.material.opacity = t < 7 ? 0.32 * ramp(t, 0.2, 2.2) : (t < 31 ? 0.3 : (t < 46 ? 0.2 : 0.28));
  brain.base.material.size = 0.0042;
  const L = control ? S.LS : S.L, other = control ? S.L : S.LS;
  for (const ly of [other.stim, other.down, other.gf]) ly.pts.visible = false;
  for (const ly of [L.stim, L.down, L.gf]) ly.pts.visible = true;
  if (control) { S.L.gf.pts.visible = true; paint(S.L.gf, () => [0.32, 0.32, 0.36]); }
  const showRun = t >= 19.6 && t < 51;
  const stimA = showRun ? ramp(t, 20.6, 22.4) : 0;
  const pulseStim = 0.75 + 0.25 * Math.sin(t * 7.0);
  paint(L.stim, () => [1.0 * stimA * pulseStim, 0.25 * stimA * pulseStim, 0.85 * stimA * pulseStim]);
  const wave = control ? 1.2 : 1.2 * ramp(t, 25.6, 29.6);
  paint(L.down, (k) => {
    const on = showRun ? smooth((wave - L.down.d[k]) / 0.18) : 0;
    const g = on * (0.25 + 0.9 * clamp(L.down.r[k] / 200));
    return [0.45 * g, 0.85 * g, 1.0 * g];
  });
  const gfOn = control ? 1 : ramp(t, 29.4, 30.2);
  const flash = 1 + 0.8 * Math.exp(-((t - 30.0) ** 2) / 0.08);
  paint(L.gf, (k) => {
    if (!showRun) return [0, 0, 0];
    if (L.gf.silenced[k]) return [0.28 * gfOn, 0.28 * gfOn, 0.3 * gfOn];
    const g = gfOn * flash * (0.9 + 0.2 * Math.sin(t * 9));
    return [1.3 * g, 0.85 * g, 0.25 * g];
  });

  // ---- adapter pulses (illustrative): giant fiber -> wings / jump legs, only in the escape run
  const pa = !control && t >= 30.2 && t < 33.5 ? win(t, 30.2, 33.5, 0.5) : 0;
  const ends = control ? [] : WINGS_LEGS.map((n) => bodyPose(P, n, simT, S.u)?.p || bc);
  drawPulses(bc, ends, 0xffc04d, t, pa, 1.3);

  // ---- looming object
  const lx = ramp(t, 20.0, 25.0);
  S.loom.visible = t >= 19.6 && t < 26.2;
  const ldir = V(0.6, 0.65, 0.22).normalize();
  S.loom.position.copy(bc).add(ldir.multiplyScalar(lerp(4.0, 0.9, lx)));
  S.loom.scale.setScalar(lerp(0.05, 0.27, lx));
  S.loom.material.uniforms.uAlpha.value = (t < 25.4 ? 1 : 1 - ramp(t, 25.4, 26.2)) * ramp(t, 19.6, 20.4);

  // ---- trail, floor
  S.trail.visible = !control && t >= 32.2 && t < 39.2;
  if (S.trail.visible) { const { f } = frameAt(S.take, simT); S.trail.geometry.setDrawRange(0, f + 1); }
  floor.visible = ring.visible = t >= 30.6 && t < 46.6;
  if (control) { floor.position.set(thorax.x, thorax.y, 0); ring.position.set(thorax.x, thorax.y, 0.01); }
  else { floor.position.set(0, 0, 0); ring.position.set(0, 0, 0.01); }

  // ---- camera
  if (t < 7) camOrbit(bc, lerp(1.3, 1.6, ramp(t, 0, 7)), lerp(12, -18, t / 7), lerp(8, 13, t / 7));
  else if (t < 19.6) camOrbit(bc, lerp(1.6, 1.75, ramp(t, 7, 19.6)), lerp(-18, 16, ramp(t, 7, 19.6)), lerp(13, 12, ramp(t, 7, 19.6)));
  else if (t < 30.6) camOrbit(bc, lerp(1.75, 1.95, ramp(t, 19.6, 30.6)), lerp(16, -14, ramp(t, 19.6, 30.6)), lerp(12, 16, ramp(t, 19.6, 30.6)));
  else if (t < 39.2) { const x = ramp(t, 30.6, 33.6); camOrbit(bc.clone().lerp(thorax, x), lerp(1.95, 11, x), lerp(-14, -55, ramp(t, 30.6, 39.2)), lerp(16, 16, x)); }
  else if (t < 45.6) camOrbit(thorax, 8.5, lerp(-120, -140, ramp(t, 39.2, 45.6)), 34);
  else camOrbit(bc, lerp(2.0, 1.75, ramp(t, 45.6, 59.5)), lerp(25, -25, ramp(t, 45.6, 59.5)), 11);

  // ---- overlays
  const fade = Math.max(win(t, 38.6, 39.8, 0.6), ramp(t, 45.0, 46.0) * (1 - ramp(t, 46.0, 46.8)),
    t >= 51 && t < 55.6 ? lerp(0, 0.88, ramp(t, 50.8, 51.6)) : 0, t >= 55.6 ? lerp(0.88, 1, ramp(t, 55.4, 56.0)) : 0);
  $('fade').style.opacity = fade;
  drawText(t);
  $('stats').style.opacity = win(t, 51.6, 55.4, 0.5);
  document.querySelectorAll('#stats .s').forEach((el, i) => { const o = win(t, 51.8 + 0.3 * i, 55.4, 0.5); el.style.opacity = o; el.style.transform = `translateY(${(1 - o) * 12}px)`; });
  const chipsA = Math.max(win(t, 8.2, 12.8, 0.6), win(t, 52.8, 55.4, 0.5));
  $('chips').style.opacity = chipsA;
  $('chips').style.top = t < 20 ? '78vh' : '';
  composer.render();
}

init().then(() => {
  renderAt(0);
  window.__film = { ready: true, duration: DURATION, renderAt };
  window.__dbg = { camera, S, brain };
  if (!CAPTURE) {
    const t0 = performance.now();
    const loop = () => { renderAt(((performance.now() - t0) / 1000) % DURATION); requestAnimationFrame(loop); };
    requestAnimationFrame(loop);
  }
}).catch((e) => { console.error(e); document.body.insertAdjacentHTML('beforeend', `<pre style="color:#f66">${e}</pre>`); window.__film = { error: String(e) }; });
