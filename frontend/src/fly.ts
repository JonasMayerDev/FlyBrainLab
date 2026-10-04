import * as THREE from 'three';

interface BufferDescriptor { byte_offset: number; count: number; item_size: number; dtype: 'float32' | 'uint16' | 'uint32' }
interface GeometryDescriptor { id: string; positions: BufferDescriptor; indices: BufferDescriptor; normals?: BufferDescriptor }
interface JointDescriptor { name: string; axis: [number, number, number]; position: [number, number, number]; reference_angle: number; wing_angle_index?: number }
interface GeomInstance { geometry_id: string; position: [number, number, number]; quaternion: [number, number, number, number]; rgba: [number, number, number, number] }
interface BodyNode { id: string; parent: string | null; position: [number, number, number]; quaternion: [number, number, number, number]; geometries: GeomInstance[]; joints: JointDescriptor[] }
interface FlyAsset { schema_version: number; units: string; buffer?: string; buffer_file?: string; geometries: GeometryDescriptor[]; nodes: BodyNode[] }

/** Author geometry and MuJoCo hinge kinematics; no procedural flapping or gait. */
export class RecordedFly extends THREE.Group {
  private articulated: { group: THREE.Group; base: THREE.Matrix4; joints: JointDescriptor[] }[] = [];
  readonly modelExtent: number;

  constructor(asset: FlyAsset, buffer: ArrayBuffer) {
    super();
    if (asset.units !== 'cm') throw new Error('Fly mesh coordinates must use centimeters.');
    const geometries = new Map<string, THREE.BufferGeometry>();
    const attribute = (descriptor: BufferDescriptor) => {
      const length = descriptor.count * descriptor.item_size;
      const array = descriptor.dtype === 'float32' ? new Float32Array(buffer, descriptor.byte_offset, length)
        : descriptor.dtype === 'uint16' ? new Uint16Array(buffer, descriptor.byte_offset, length)
        : new Uint32Array(buffer, descriptor.byte_offset, length);
      return new THREE.BufferAttribute(array, descriptor.item_size);
    };
    for (const descriptor of asset.geometries) {
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', attribute(descriptor.positions));
      geometry.setIndex(attribute(descriptor.indices));
      if (descriptor.normals) geometry.setAttribute('normal', attribute(descriptor.normals));
      else geometry.computeVertexNormals();
      geometry.computeBoundingSphere();
      geometries.set(descriptor.id, geometry);
    }
    const groups = new Map<string, THREE.Group>();
    for (const node of asset.nodes) {
      const group = new THREE.Group(); group.name = node.id; group.matrixAutoUpdate = false;
      const base = new THREE.Matrix4().compose(new THREE.Vector3().fromArray(node.position), new THREE.Quaternion().fromArray(node.quaternion), new THREE.Vector3(1, 1, 1));
      group.matrix.copy(base);
      groups.set(node.id, group);
      this.articulated.push({ group, base, joints: node.joints ?? [] });
      for (const instance of node.geometries ?? []) {
        const geometry = geometries.get(instance.geometry_id);
        if (!geometry) throw new Error(`Missing fly mesh: ${instance.geometry_id}`);
        const [r, g, b, opacity] = instance.rgba;
        const material = new THREE.MeshStandardMaterial({ color: new THREE.Color(r, g, b), roughness: 0.56, metalness: 0,
          opacity, transparent: opacity < 1, depthWrite: opacity >= 1, side: THREE.DoubleSide });
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.fromArray(instance.position); mesh.quaternion.fromArray(instance.quaternion);
        group.add(mesh);
      }
    }
    for (const node of asset.nodes) {
      const group = groups.get(node.id)!;
      const parent = node.parent ? groups.get(node.parent) : undefined;
      (parent ?? this).add(group);
    }
    this.updateWings();
    this.updateMatrixWorld(true);
    this.modelExtent = new THREE.Box3().setFromObject(this).getSize(new THREE.Vector3()).length();
  }

  updateWings(angles?: number[]): void {
    for (const body of this.articulated) {
      body.group.matrix.copy(body.base);
      for (const joint of body.joints) {
        const recorded = joint.wing_angle_index === undefined ? undefined : angles?.[joint.wing_angle_index];
        const reference = joint.reference_angle ?? 0;
        const angle = typeof recorded === 'number' && Number.isFinite(recorded) ? recorded - reference : 0;
        if (!angle) continue;
        const pivot = new THREE.Vector3().fromArray(joint.position);
        // MuJoCo: fixed body transform, then ordered intrinsic right-handed hinges.
        const rotation = new THREE.Matrix4().makeRotationAxis(new THREE.Vector3().fromArray(joint.axis).normalize(), angle);
        body.group.matrix.multiply(new THREE.Matrix4().makeTranslation(pivot.x, pivot.y, pivot.z))
          .multiply(rotation).multiply(new THREE.Matrix4().makeTranslation(-pivot.x, -pivot.y, -pivot.z));
      }
      body.group.matrixWorldNeedsUpdate = true;
    }
  }
}

export async function loadRecordedFly(): Promise<RecordedFly> {
  const base = `${import.meta.env.BASE_URL}models/flybody/`;
  const response = await fetch(`${base}scene.json`);
  if (!response.ok) throw new Error(`Fly geometry manifest unavailable (${response.status}).`);
  const asset = await response.json() as FlyAsset;
  const binary = await fetch(`${base}${asset.buffer ?? asset.buffer_file ?? 'geometry.bin'}`);
  if (!binary.ok) throw new Error(`Fly geometry buffer unavailable (${binary.status}).`);
  return new RecordedFly(asset, await binary.arrayBuffer());
}
