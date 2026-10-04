import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import type { Replay } from './types';

export class NeuralScene {
  private renderer: THREE.WebGLRenderer;
  private scene = new THREE.Scene();
  private camera = new THREE.PerspectiveCamera(40, 1, 0.1, 50);
  private controls: OrbitControls;
  private nodes?: THREE.InstancedMesh;
  private positions: THREE.Vector3[] = [];
  private run?: Replay;
  private dummy = new THREE.Object3D();
  private raycaster = new THREE.Raycaster();
  private observer: ResizeObserver;
  private guides: THREE.Group;
  private body: THREE.Group;
  private path?: THREE.Line;
  private bodyGrid: THREE.GridHelper;
  private mode: 'neural' | 'body' = 'neural';
  private selectedId?: string;
  private onSelect: (id: string) => void;
  private colors = { quiet: new THREE.Color('#496065'), target: new THREE.Color('#d5f78c'), active: new THREE.Color('#ffffff'), selected: new THREE.Color('#7bddcb') };

  constructor(private container: HTMLElement, onSelect: (id: string) => void) {
    this.onSelect = onSelect;
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setClearColor('#101a1b', 1);
    this.renderer.domElement.setAttribute('aria-label', 'Interactive abstract neuron view. Drag to rotate, scroll to zoom; use the neuron list below for keyboard selection.');
    this.renderer.domElement.setAttribute('role', 'img');
    container.append(this.renderer.domElement);
    this.camera.position.set(0.5, 0.5, 6.7);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.enablePan = false;
    this.controls.minDistance = 3;
    this.controls.maxDistance = 11;
    this.guides = this.createGuides();
    this.scene.add(this.guides);
    this.body = this.createBodyMarker();
    this.body.visible = false;
    this.scene.add(this.body);
    this.bodyGrid = new THREE.GridHelper(8, 24, '#315b4e', '#1b3530');
    this.bodyGrid.rotation.x = Math.PI / 2;
    this.bodyGrid.visible = false;
    this.scene.add(this.bodyGrid);
    this.scene.add(new THREE.HemisphereLight('#f0ffe0', '#213a3e', 2));
    const light = new THREE.DirectionalLight('#efffe4', 3);
    light.position.set(2, 4, 3);
    this.scene.add(light);
    this.observer = new ResizeObserver(() => this.resize());
    this.observer.observe(container);
    this.resize();
    let start: [number, number] | null = null;
    this.renderer.domElement.addEventListener('pointerdown', event => { start = [event.clientX, event.clientY]; });
    this.renderer.domElement.addEventListener('pointerup', event => {
      if (!start || Math.hypot(event.clientX - start[0], event.clientY - start[1]) > 5 || !this.nodes || this.mode === 'body') return;
      const bounds = this.renderer.domElement.getBoundingClientRect();
      this.raycaster.setFromCamera(new THREE.Vector2((event.clientX - bounds.left) / bounds.width * 2 - 1, -(event.clientY - bounds.top) / bounds.height * 2 + 1), this.camera);
      const hit = this.raycaster.intersectObject(this.nodes)[0];
      if (hit?.instanceId !== undefined && this.run) this.onSelect(this.run.graph.nodes[hit.instanceId].id);
    });
  }

  private createGuides(): THREE.Group {
    const group = new THREE.Group();
    const material = new THREE.LineBasicMaterial({ color: '#284145', transparent: true, opacity: 0.7 });
    for (const axis of [0, 1, 2]) {
      const points = Array.from({ length: 129 }, (_, i) => {
        const angle = i / 128 * Math.PI * 2;
        return axis === 0 ? new THREE.Vector3(Math.cos(angle) * 1.9, Math.sin(angle) * 1.4, 0)
          : axis === 1 ? new THREE.Vector3(Math.cos(angle) * 1.9, 0, Math.sin(angle) * 1.2)
          : new THREE.Vector3(0, Math.cos(angle) * 1.4, Math.sin(angle) * 1.2);
      });
      group.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), material));
    }
    const grid = new THREE.GridHelper(8, 18, '#284145', '#1a2d30');
    grid.position.y = -1.8;
    group.add(grid);
    return group;
  }

  private createBodyMarker(): THREE.Group {
    const group = new THREE.Group();
    const material = new THREE.MeshStandardMaterial({ color: '#d5f78c', roughness: 0.45 });
    const root = new THREE.Mesh(new THREE.SphereGeometry(0.15, 20, 12), material);
    group.add(root);
    group.add(new THREE.AxesHelper(0.6));
    return group;
  }

  load(run: Replay): void {
    this.run = run;
    if (this.nodes) {
      this.scene.remove(this.nodes);
      this.nodes.geometry.dispose();
      (this.nodes.material as THREE.Material).dispose();
    }
    this.nodes = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 10, 6), new THREE.MeshBasicMaterial({ color: '#ffffff' }), run.graph.nodes.length);
    this.positions = run.graph.nodes.map((node, index) => {
      // Deterministic Fibonacci layout: actual IDs, explicitly non-anatomical positions.
      const y = 1 - (index + 0.5) / run.graph.nodes.length * 2;
      const radius = Math.sqrt(1 - y * y);
      const angle = index * Math.PI * (3 - Math.sqrt(5));
      if (node.target) return new THREE.Vector3(Math.sin(index * 2.4) * 0.55, Math.cos(index * 2.4) * 0.3, 0.5);
      return new THREE.Vector3(Math.cos(angle) * radius * 1.8, y * 1.25, Math.sin(angle) * radius * 1.1);
    });
    this.scene.add(this.nodes);
    if (this.path) { this.scene.remove(this.path); this.path.geometry.dispose(); (this.path.material as THREE.Material).dispose(); this.path = undefined; }
    if (run.body?.states?.length) {
      this.path = new THREE.Line(new THREE.BufferGeometry().setFromPoints(run.body.states.map(state => new THREE.Vector3().fromArray(state.position))), new THREE.LineBasicMaterial({ color: '#58805c', transparent: true, opacity: 0.55 }));
      this.scene.add(this.path);
    }
    this.selectedId = run.metadata.stimulated_neuron_ids[0];
    this.setMode('neural');
  }

  setMode(mode: 'neural' | 'body'): void {
    this.mode = mode;
    if (this.nodes) this.nodes.visible = mode === 'neural';
    this.body.visible = mode === 'body';
    this.guides.visible = mode === 'neural';
    this.bodyGrid.visible = mode === 'body';
    if (this.path) this.path.visible = mode === 'body';
    this.reset();
  }

  select(id: string): void { this.selectedId = id; }
  reset(): void {
    if (this.mode === 'body') {
      const points = this.run?.body?.states?.map(state => new THREE.Vector3().fromArray(state.position)) ?? [];
      const bounds = new THREE.Box3().setFromPoints(points);
      const center = points.length ? bounds.getCenter(new THREE.Vector3()) : new THREE.Vector3(0.35, 0, 0.8);
      const extent = bounds.getSize(new THREE.Vector3());
      const distance = Math.max(3.8, extent.length() * 1.25);
      this.camera.up.set(0, 0, 1); this.camera.position.copy(center).add(new THREE.Vector3(distance * 0.5, -distance, distance * 0.55));
      this.controls.target.copy(center); this.controls.minDistance = 1; this.controls.maxDistance = Math.max(11, distance * 2);
      this.bodyGrid.position.set(center.x, center.y, 0);
    } else {
      this.camera.up.set(0, 1, 0); this.camera.position.set(0.5, 0.5, 6.7); this.controls.target.set(0, 0, 0); this.controls.minDistance = 3;
    }
  }

  render(timeMs: number): void {
    if (this.run && this.nodes) {
      const recent = new Map<string, number>();
      const windowMs = Math.max(0.5, this.run.metadata.duration_ms * 0.015);
      for (const event of this.run.activity.events) {
        if (event.time_ms > timeMs) break;
        if (event.time_ms >= timeMs - windowMs) recent.set(event.neuron_id, (timeMs - event.time_ms) / windowMs);
      }
      this.run.graph.nodes.forEach((node, index) => {
        const pulse = recent.has(node.id) ? 1 - recent.get(node.id)! : 0;
        this.dummy.position.copy(this.positions[index]);
        const scale = (node.target ? 0.06 : node.spike_count ? 0.036 : 0.022) + pulse * 0.05;
        this.dummy.scale.setScalar(scale);
        this.dummy.updateMatrix();
        this.nodes!.setMatrixAt(index, this.dummy.matrix);
        const color = node.id === this.selectedId || node.readout ? this.colors.selected : node.target ? this.colors.target : this.colors.quiet;
        this.nodes!.setColorAt(index, color.clone().lerp(this.colors.active, pulse));
      });
      this.nodes.instanceMatrix.needsUpdate = true;
      if (this.nodes.instanceColor) this.nodes.instanceColor.needsUpdate = true;
      const states = this.run.body?.states;
      if (states?.length) {
        let next = states.findIndex(state => state.time_ms > timeMs);
        if (next < 0) next = states.length - 1;
        const a = states[Math.max(0, next - 1)], b = states[next];
        const fraction = b.time_ms === a.time_ms ? 0 : Math.min(1, Math.max(0, (timeMs - a.time_ms) / (b.time_ms - a.time_ms)));
        this.body.position.fromArray(a.position).lerp(new THREE.Vector3().fromArray(b.position), fraction);
        if (a.quaternion && b.quaternion) this.body.quaternion.fromArray(a.quaternion).slerp(new THREE.Quaternion().fromArray(b.quaternion), fraction);
      }
    }
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }

  private resize(): void {
    const width = this.container.clientWidth, height = this.container.clientHeight;
    if (!width || !height) return;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }
}
