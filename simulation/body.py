"""Real headless Flybody physics runs and replay exports; no flight claim.

Run in the isolated body environment documented in docs/BODY_INTEGRATION.md.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import platform
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
FLYBODY_COMMIT = "d015e9bfe441bd90ae431bac24c55cb74bdbce26"


def configure_headless() -> None:
    os.environ.setdefault("MUJOCO_GL", "disable")
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".runtime/mplconfig"))
    os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".runtime/body-cache"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def runtime_manifest() -> dict:
    """Hash installed model/source files, avoiding a claim from package name only."""
    import flybody
    package = Path(flybody.__file__).parent
    files = sorted(p for p in package.rglob("*") if p.suffix in {".py", ".xml", ".obj"})
    hashes = {str(p.relative_to(package)): sha256(p) for p in files}
    fingerprint = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    result = {"schema_version": 1, "model": "Flybody Drosophila melanogaster",
              "repository": "https://github.com/TuragaLab/flybody", "commit": FLYBODY_COMMIT,
              "license": "Apache-2.0", "installed_file_sha256": hashes,
              "installed_source_fingerprint_sha256": fingerprint,
              "versions": {"python": platform.python_version(), **{p: version(p) for p in
                            ("flybody", "dm_control", "mujoco", "numpy", "scipy", "h5py")}}}
    expected_path = ROOT / "data/body/runtime_manifest.json"
    if expected_path.exists():
        expected = json.loads(expected_path.read_text())
        if (result["versions"] != expected["versions"] or
                fingerprint != expected["installed_source_fingerprint_sha256"]):
            raise ValueError("Body runtime differs from pinned versions/source hashes; reinstall requirements.body.lock")
    return result


def make_environment(seed: int, diagnostic: dict | None = None):
    configure_headless()
    import numpy as np
    from flybody.fly_envs import flight_imitation
    # Existing inference-mode reference only initializes the task. Export the
    # walker body, never the ghost/reference trajectory, as the measured result.
    pattern_path = (ROOT / ".runtime/body-published-data/wing_pattern_fmech.npy"
                    if diagnostic and diagnostic.get("published_wing_pattern") else None)
    env = flight_imitation(random_state=np.random.RandomState(seed),
                           wpg_pattern_path=str(pattern_path) if pattern_path else None,
                           terminal_com_dist=float("inf"))
    if diagnostic and diagnostic.get("extend_reference"):
        from flybody.tasks.synthetic_trajectories import constant_speed_trajectory
        steps = math.ceil(diagnostic["duration_ms"] / (1000 * env.control_timestep())) + 20
        reference, velocity = constant_speed_trajectory(
            n_steps=steps, speed=20, init_pos=(0, 0, 1), body_rot_angle_y=-47.5,
            control_timestep=env.control_timestep())
        # Extend a task reference only. It never sets measured body positions
        # after reset and provides no control action to the zero-action policy.
        env.task._traj_generator.set_next_trajectory(reference, velocity)
    env.reset()
    if diagnostic and diagnostic.get("disable_task_termination"):
        # Explicit bounded diagnostic: retain composer 0.6s limit and finite-
        # state checks but bypass author task conditions such as low thorax.
        env.task.check_termination = lambda physics: False
    return env


def capture_state(env, adapter_rate_hz: float = 0., amplitude_factor: float = 1.) -> dict:
    import numpy as np
    physics = env.physics
    position, quaternion_wxyz = env.task.walker.get_pose(physics)
    velocity = np.asarray(physics.bind(env.task._root_joint).qvel)
    wing_angles = np.asarray(physics.bind(env.task._wing_joints).qpos)
    # MuJoCo/Flybody uses wxyz; browser Three.js quaternion uses xyzw.
    quaternion_xyzw = np.asarray(quaternion_wxyz)[[1, 2, 3, 0]]
    values = [*position, *quaternion_xyzw, *velocity, *wing_angles,
              adapter_rate_hz, amplitude_factor]
    if not all(math.isfinite(float(v)) for v in values):
        raise ValueError("Nonfinite physical state; refusing a successful replay export")
    return {"time_ms": round(1000 * float(physics.time()), 9),
            "position": [float(x) for x in position],
            "quaternion": quaternion_xyzw.tolist(),
            "linear_velocity_cm_s": velocity[:3].tolist(),
            "angular_velocity_rad_s": velocity[3:].tolist(),
            "wing_angles_rad": wing_angles.tolist(),
            "qpos": np.asarray(physics.data.qpos).tolist(),
            "qvel": np.asarray(physics.data.qvel).tolist(),
            "thorax_height_cm": float(env.task.walker.observables.thorax_height(physics)),
            "adapter_rate_hz": float(adapter_rate_hz),
            "wing_yaw_amplitude_factor": float(amplitude_factor)}


def termination_checks(env) -> dict:
    import numpy as np
    from flybody.tasks.constants import _TERMINAL_HEIGHT, _TERMINAL_QACC
    height = float(env.task.walker.observables.thorax_height(env.physics))
    acceleration = float(np.linalg.norm(env.physics.data.qacc))
    return {"reference_end_reached": bool(env.task._reached_traj_end),
            "reference_end_step": int(env.task._traj_timesteps),
            "reference_end_ms": 1000 * env.control_timestep() * env.task._traj_timesteps,
            "thorax_height_cm": height, "thorax_height_threshold_cm": _TERMINAL_HEIGHT,
            "thorax_below_threshold": height < _TERMINAL_HEIGHT,
            "qacc_norm": acceleration, "qacc_threshold": _TERMINAL_QACC,
            "acceleration_above_threshold": acceleration > _TERMINAL_QACC}


def trajectory_metrics(states: list[dict]) -> dict:
    import numpy as np
    positions = np.array([s["position"] for s in states])
    angles = np.array([s["wing_angles_rad"] for s in states])
    return {"sample_count": len(states), "actual_duration_ms": states[-1]["time_ms"],
            "root_displacement_cm": float(np.linalg.norm(positions[-1] - positions[0])),
            "root_path_length_cm": float(np.linalg.norm(np.diff(positions, axis=0), axis=1).sum()),
            "root_height_change_cm": float(positions[-1, 2] - positions[0, 2]),
            "minimum_root_height_cm": float(positions[:, 2].min()),
            "minimum_thorax_height_cm": min(s["thorax_height_cm"] for s in states),
            "wing_yaw_peak_to_peak_rad": np.ptp(angles[:, [0, 3]], axis=0).tolist(),
            "maximum_adapter_rate_hz": max(s["adapter_rate_hz"] for s in states),
            "maximum_wing_yaw_amplitude_factor": max(s["wing_yaw_amplitude_factor"] for s in states)}


def run_body(duration_ms: float = 200, seed: int = 42, output_dir: Path | None = None,
             adapter=None, neural_provenance: dict | None = None,
             diagnostic: dict | None = None) -> dict:
    if not 1 <= duration_ms <= 200:
        raise ValueError("Body probe duration must be 1..200 ms")
    if diagnostic:
        diagnostic = {**diagnostic, "duration_ms": duration_ms}
        if diagnostic.get("disable_task_termination") and not diagnostic.get("extend_reference"):
            raise ValueError("Termination-bypass diagnostic requires a safely extended task reference")
    configure_headless()
    import numpy as np
    kind = "diagnostic-" if diagnostic else "coupled-" if adapter else "baseline-"
    run_id = "body-" + kind + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:6]
    output = output_dir or ROOT / "data/body" / run_id
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    manifest = runtime_manifest()
    record = {"schema_version": 1, "run_id": run_id, "status": "running",
              "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "run_kind": "coupled_simulation" if adapter else "body_simulation",
              "requested_duration_ms": duration_ms, "seed": seed,
              "diagnostic_configuration": diagnostic,
              "model": manifest["model"], "model_commit": FLYBODY_COMMIT,
              "model_fingerprint_sha256": manifest["installed_source_fingerprint_sha256"],
              "versions": manifest["versions"],
              "controller": "author WingBeatPatternGenerator; approximate pattern; no trained RL policy",
              "controller_base_frequency_hz": 218.,
              "loop": "open-loop recorded spike replay" if adapter else "open-loop controller baseline",
              "sensor_feedback": False, "flight_validated": False,
              "body_connected": bool(adapter), "neural_provenance": neural_provenance,
              "result_path": str(output.relative_to(ROOT)),
              "limitations": ["Default wing pattern is an author-provided test approximation.",
                              "Initial position/velocity are task reference initialization, not generated by the brain.",
                              "Floor collision is disabled by the author flight task.",
                              "A moving body is not evidence of stable or brain-generated flight.",
                              "No sensory feedback or calibrated ventral nerve cord/muscle mapping is present."]}
    if diagnostic and diagnostic.get("published_wing_pattern"):
        pattern_path = ROOT / ".runtime/body-published-data/wing_pattern_fmech.npy"
        record["controller"] = "author WingBeatPatternGenerator; published fmech wing pattern; no trained RL policy"
        record["wing_pattern_sha256"] = sha256(pattern_path)
        record["limitations"][0] = "Published author wing pattern is used without its trained flight policy."
    states = []
    try:
        env = make_environment(seed, diagnostic)
        if adapter:
            adapter.attach(env)
            record["adapter"] = adapter.provenance()
        record.update(physics_timestep_ms=1000 * env.physics.timestep(),
                      control_timestep_ms=1000 * env.control_timestep(),
                      action_dimensions=env.action_spec().shape[0],
                      action_names=env.action_spec().name.split("\t"),
                      wing_joint_order=[j.name for j in env.task._wing_joints],
                      gravity_cm_s2=np.asarray(env.physics.model.opt.gravity).tolist(),
                      initial_root_velocity=np.asarray(env.physics.bind(env.task._root_joint).qvel).tolist())
        states.append(capture_state(env))
        terminated = False
        for _ in range(round(duration_ms / record["control_timestep_ms"])):
            rate, factor = adapter.update(env.physics.time()) if adapter else (0., 1.)
            # before_step mutates the passed action; always allocate a fresh zero
            # vector so controller forces cannot accumulate between steps.
            step = env.step(np.zeros(env.action_spec().shape, dtype=float))
            states.append(capture_state(env, rate, factor))
            if step.last():
                terminated = True
                break
        checks = termination_checks(env)
        cause = ("reference trajectory end" if checks["reference_end_reached"] else
                 "thorax below height threshold" if checks["thorax_below_threshold"] else
                 "acceleration threshold" if checks["acceleration_above_threshold"] else
                 "other author task termination condition")
        record.update(status="completed", task_terminated_early=terminated,
                      task_termination_checks=checks,
                      termination_reason=cause if terminated else "requested probe horizon",
                      metrics=trajectory_metrics(states))
        trajectory = {"schema_version": 1, "recorded_simulation": True,
                      "run_id": run_id, "units": {"position": "cm", "time": "ms", "angles": "rad"},
                      "axis_convention": "right-handed MuJoCo world; z-up; quaternion xyzw",
                      "source": "measured walker physics states, not ghost/reference trajectory",
                      "model": record["model"], "model_commit": FLYBODY_COMMIT,
                      "controller": record["controller"], "loop": record["loop"],
                      "diagnostic_configuration": diagnostic,
                      "adapter": record.get("adapter"), "flight_validated": False,
                      "states": states}
        write_json(output / "trajectory.json", trajectory)
        write_json(output / "model_manifest.json", manifest)
        record["trajectory_sha256"] = sha256(output / "trajectory.json")
    except Exception as exc:
        record.update(status="failed", error_type=type(exc).__name__, error=str(exc),
                      samples_before_failure=len(states))
        raise
    finally:
        record.update(ended_at_utc=datetime.now(timezone.utc).isoformat(),
                      wall_seconds=round(time.monotonic() - started, 4))
        write_json(output / "run.json", record)
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration-ms", type=float, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--extend-reference", action="store_true",
                        help="Separate diagnostic: extend synthetic reference preserving initial conditions")
    parser.add_argument("--disable-task-termination", action="store_true",
                        help="Separate diagnostic only: explicitly bypass author termination checks")
    parser.add_argument("--published-wing-pattern", action="store_true",
                        help="Separate diagnostic: downloaded author fmech pattern, no learned policy")
    args = parser.parse_args()
    diagnostic = ({"extend_reference": args.extend_reference,
                   "disable_task_termination": args.disable_task_termination,
                   "published_wing_pattern": args.published_wing_pattern}
                  if args.extend_reference or args.disable_task_termination or args.published_wing_pattern else None)
    print(json.dumps(run_body(args.duration_ms, args.seed, diagnostic=diagnostic), indent=2, allow_nan=False))
