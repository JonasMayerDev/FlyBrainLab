#!/usr/bin/env python3
"""Export pinned author meshes and fixed-pose kinematics; never advance physics.

Run with .runtime/body-venv/bin/python scripts/export_flybody_geometry.py.
Geometry comes from the actual flight task, including retracted legs and its
wing-frame changes. The web replay supplies root pose and six measured wing
angles; other joint angles stay at the author's compiled neutral reference.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend/public/models/flybody"
os.environ.setdefault("MUJOCO_GL", "disable")
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".runtime/mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".runtime/body-cache"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def main() -> None:
    import flybody
    import mujoco
    import numpy as np
    from dm_control import mjcf
    from flybody.fly_envs import flight_imitation

    pinned = json.loads((ROOT / "data/body/runtime_manifest.json").read_text())
    package = Path(flybody.__file__).parent
    hashes = {str(p.relative_to(package)): digest(p) for p in sorted(package.rglob("*"))
              if p.suffix in {".py", ".xml", ".obj"}}
    fingerprint = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    if fingerprint != pinned["installed_source_fingerprint_sha256"]:
        raise ValueError("Installed Flybody differs from the recorded source")

    # Build/compile only: no Environment.reset, step, policy or integration.
    environment = flight_imitation(random_state=np.random.RandomState(42))
    physics = mjcf.Physics.from_mjcf_model(environment.task.root_entity.mjcf_model)
    model = physics.model
    wing_names = [f"wing_{axis}_{side}" for side in ("left", "right")
                  for axis in ("yaw", "roll", "pitch")]
    root_id = model.name2id("walker/", "body")
    body_ids = [i for i in range(model.nbody)
                if (model.id2name(i, "body") or "").startswith("walker/")]
    geom_ids = [i for i in range(model.ngeom)
                if int(model.geom_bodyid[i]) in body_ids
                and int(model.geom_type[i]) == int(mujoco.mjtGeom.mjGEOM_MESH)]
    mesh_ids = sorted({int(model.geom_dataid[i]) for i in geom_ids})
    OUT.mkdir(parents=True, exist_ok=True)
    binary = bytearray()

    def pack(array, dtype: str, item_size: int) -> dict:
        while len(binary) % 4:
            binary.append(0)
        a = np.asarray(array, dtype={"float32": "<f4", "uint16": "<u2"}[dtype])
        descriptor = {"byte_offset": len(binary), "count": int(a.size // item_size),
                      "item_size": item_size, "dtype": dtype}
        binary.extend(a.tobytes())
        return descriptor

    geometries = []
    for mesh_id in mesh_ids:
        first, count = int(model.mesh_vertadr[mesh_id]), int(model.mesh_vertnum[mesh_id])
        vertices = np.asarray(model.mesh_vert[first:first + count], dtype=np.float32)
        # Exactly equal positions are welded. No vertex is moved, no face removed.
        unique, inverse = np.unique(vertices, axis=0, return_inverse=True)
        first_face = int(model.mesh_faceadr[mesh_id])
        faces = np.asarray(model.mesh_face[first_face:first_face + int(model.mesh_facenum[mesh_id])])
        indices = inverse[faces]
        if len(unique) > 65535 or np.any(indices < 0) or np.any(indices >= len(unique)):
            raise ValueError("Index format/range exceeded")
        geometries.append({"id": model.id2name(mesh_id, "mesh"),
                           "positions": pack(unique, "float32", 3),
                           "indices": pack(indices, "uint16", 1),
                           "vertex_count": len(unique), "triangle_count": len(faces)})

    quat_xyzw = lambda q: np.asarray(q)[[1, 2, 3, 0]].tolist()
    nodes = []
    for body_id in body_ids:
        name = model.id2name(body_id, "body")
        joints = []
        for j in range(int(model.body_jntadr[body_id]),
                       int(model.body_jntadr[body_id] + model.body_jntnum[body_id])):
            if int(model.jnt_type[j]) == int(mujoco.mjtJoint.mjJNT_FREE):
                continue
            if int(model.jnt_type[j]) != int(mujoco.mjtJoint.mjJNT_HINGE):
                raise ValueError("Unexpected non-hinge body joint")
            joint_name = model.id2name(j, "joint").removeprefix("walker/")
            joint = {"name": joint_name, "axis": model.jnt_axis[j].tolist(),
                     "position": model.jnt_pos[j].tolist(),
                     "reference_angle": float(model.qpos0[model.jnt_qposadr[j]]),
                     "qpos_address": int(model.jnt_qposadr[j])}
            if joint_name in wing_names:
                joint["wing_angle_index"] = wing_names.index(joint_name)
            joints.append(joint)
        geoms = []
        for geom_id in geom_ids:
            if int(model.geom_bodyid[geom_id]) != body_id:
                continue
            material_id = int(model.geom_matid[geom_id])
            rgba = model.geom_rgba[geom_id]
            if material_id >= 0 and np.allclose(rgba, [0.5, 0.5, 0.5, 1.]):
                rgba = model.mat_rgba[material_id]
            geoms.append({"id": model.id2name(geom_id, "geom"),
                          "geometry_id": model.id2name(int(model.geom_dataid[geom_id]), "mesh"),
                          "position": model.geom_pos[geom_id].tolist(),
                          "quaternion": quat_xyzw(model.geom_quat[geom_id]),
                          "rgba": np.asarray(rgba).tolist()})
        nodes.append({"id": name,
                      "parent": None if body_id == root_id else model.id2name(int(model.body_parentid[body_id]), "body"),
                      "position": [0., 0., 0.] if body_id == root_id else model.body_pos[body_id].tolist(),
                      "quaternion": [0., 0., 0., 1.] if body_id == root_id else quat_xyzw(model.body_quat[body_id]),
                      "recorded_root": body_id == root_id, "geometries": geoms, "joints": joints})

    # Independent browser-style matrix composition vs MuJoCo kinematics.
    # Only root and measured wings are dynamic; all other angles are fixed.
    def transform(position, quaternion):
        result = np.eye(4)
        wxyz = np.asarray(quaternion)[[3, 0, 1, 2]]
        rotation = np.zeros(9)
        mujoco.mju_quat2Mat(rotation, wxyz)
        result[:3, :3] = rotation.reshape(3, 3)
        result[:3, 3] = position
        return result

    trajectory_path = ROOT / "data/body/body-coupled-policy-20261004T010044Z-de8a13/trajectory.json"
    trajectory = json.loads(trajectory_path.read_text())
    validations = []
    maximum_error = 0.
    for time_ms in [0., 10., 100., 200.]:
        state = min(trajectory["states"], key=lambda s: abs(s["time_ms"] - time_ms))
        physics.data.qpos[:] = model.qpos0
        root_joint = int(model.body_jntadr[root_id])
        adr = int(model.jnt_qposadr[root_joint])
        physics.data.qpos[adr:adr + 3] = state["position"]
        physics.data.qpos[adr + 3:adr + 7] = np.asarray(state["quaternion"])[[3, 0, 1, 2]]
        for index, name in enumerate(wing_names):
            jid = model.name2id("walker/" + name, "joint")
            physics.data.qpos[model.jnt_qposadr[jid]] = state["wing_angles_rad"][index]
        mujoco.mj_kinematics(model.ptr, physics.data.ptr)
        matrices = {}
        body_error = geom_error = 0.
        for node, body_id in zip(nodes, body_ids):
            if node["recorded_root"]:
                world = transform(state["position"], state["quaternion"])
            else:
                world = matrices[node["parent"]] @ transform(node["position"], node["quaternion"])
                for joint in node["joints"]:
                    angle = state["wing_angles_rad"][joint["wing_angle_index"]] if "wing_angle_index" in joint else joint["reference_angle"]
                    delta = angle - joint["reference_angle"]
                    quaternion = [*(np.asarray(joint["axis"]) * np.sin(delta / 2)), np.cos(delta / 2)]
                    pivot = np.asarray(joint["position"])
                    world = (world @ transform(pivot, [0, 0, 0, 1])
                             @ transform([0, 0, 0], quaternion)
                             @ transform(-pivot, [0, 0, 0, 1]))
            matrices[node["id"]] = world
            expected = np.eye(4)
            expected[:3, :3] = physics.data.xmat[body_id].reshape(3, 3)
            expected[:3, 3] = physics.data.xpos[body_id]
            body_error = max(body_error, float(np.max(np.abs(world - expected))))
            for geom in node["geometries"]:
                gid = model.name2id(geom["id"], "geom")
                rendered = world @ transform(geom["position"], geom["quaternion"])
                expected[:3, :3] = physics.data.geom_xmat[gid].reshape(3, 3)
                expected[:3, 3] = physics.data.geom_xpos[gid]
                geom_error = max(geom_error, float(np.max(np.abs(rendered - expected))))
        maximum_error = max(maximum_error, body_error, geom_error)
        validations.append({"time_ms": state["time_ms"], "maximum_body_matrix_error": body_error,
                            "maximum_geom_matrix_error": geom_error})
    if maximum_error > 1e-10:
        raise ValueError(f"Exported hierarchy differs from MuJoCo kinematics: {maximum_error}")

    scene = {"schema_version": 1, "units": "cm", "angles": "radians",
             "axes": {"handedness": "right", "up": "+z", "forward": "+x", "left": "+y"},
             "quaternion_order": "xyzw", "buffer": "geometry.bin",
             "source": {"repository": pinned["repository"], "commit": pinned["commit"],
                        "license": "Apache-2.0", "fingerprint_sha256": fingerprint},
             "mesh_transform_rule": "Compiled vertices and geom transforms already include mesh scale/centering/alignment. Apply only geom position/quaternion once.",
             "pose_rule": "Root pose and six wing angles are recorded. Other joints use fixed compiled neutral reference; legs are author flight-task retracted geometry. Fixed parts are not measured joint motion.",
             "joint_transform_rule": "body base transform then listed hinge rotations in order, angle minus reference, positive right-hand rule about body-local axes/pivots",
             "wing_joint_order": wing_names, "geometries": geometries, "nodes": nodes}
    (OUT / "geometry.bin").write_bytes(binary)
    write_json(OUT / "scene.json", scene)
    shutil.copyfile(ROOT / "data/body/LICENSE.flybody", OUT / "LICENSE")
    (OUT / "NOTICE.txt").write_text(
        "Flybody fruit-fly geometry, TuragaLab and Flybody contributors.\n"
        f"Source: {pinned['repository']}/tree/{pinned['commit']}/flybody/fruitfly/assets\n"
        "Licensed under Apache License 2.0; the original license is in LICENSE.\n"
        "Modified by FlyBrainLab: compiled flight-task hierarchy exported to JSON; "
        "original mesh vertices deduplicated by equal position and packed as float32/uint16. "
        "No triangles removed, geometry decimation, new simulation or controller training. "
        "Surface normals are recomputed by the renderer; authored material RGBA retained.\n"
        "This geometry license is separate from the GPL-licensed published policy supplement.\n")
    sources = {name: hashes[name] for name in hashes
               if name.startswith("fruitfly/assets/") and name.endswith((".obj", ".xml"))}
    write_json(OUT / "manifest.json", {
        "schema_version": 1, "source_repository": pinned["repository"], "source_commit": pinned["commit"],
        "license": "Apache-2.0", "license_file": "LICENSE", "notice_file": "NOTICE.txt",
        "source_license_url": f"{pinned['repository']}/blob/{pinned['commit']}/LICENSE",
        "source_file_sha256": sources, "installed_source_fingerprint_sha256": fingerprint,
        "conversion": "Original triangles preserved; exact duplicate compiled float32 positions welded, uint16 indices. Compiled centimeter mesh transforms preserved.",
        "output_files": {name: {"bytes": (OUT / name).stat().st_size, "sha256": digest(OUT / name)}
                         for name in ["scene.json", "geometry.bin", "LICENSE", "NOTICE.txt"]},
        "mesh_count": len(geometries), "body_node_count": len(nodes),
        "triangle_count": sum(g["triangle_count"] for g in geometries),
        "vertex_count": sum(g["vertex_count"] for g in geometries),
        "fixed_non_wing_reference": True, "new_simulation_performed": False,
        "kinematics_validation": {"source_trajectory": str(trajectory_path.relative_to(ROOT)),
                                  "source_trajectory_sha256": digest(trajectory_path),
                                  "method": "MuJoCo mj_kinematics only; fixed nonwing reference plus recorded root and wing poses; independent matrix composition for every body and mesh geom",
                                  "maximum_matrix_error": maximum_error, "samples": validations}})
    print(json.dumps({"path": str(OUT), "binary_bytes": len(binary),
                      "meshes": len(geometries), "triangles": sum(g["triangle_count"] for g in geometries),
                      "validation_max_error": maximum_error}))


if __name__ == "__main__":
    main()
