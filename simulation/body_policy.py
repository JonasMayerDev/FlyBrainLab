"""Inference-only wrapper for the authors' published flight SavedModel.

Matches their SinglePrecision/CanonicalSpec wrappers and deterministic mean
action without installing the Acme training framework. No training occurs.
"""
from __future__ import annotations

from importlib.metadata import version
import json
import os

from simulation.body import ROOT, sha256


class PublishedFlightPolicy:
    def __init__(self, action_spec):
        os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "1")
        os.environ.setdefault("TF_NUM_INTEROP_THREADS", "1")
        os.environ.setdefault("KERAS_HOME", str(ROOT / ".runtime/body-keras"))
        pinned = {}
        for line in (ROOT / "requirements.body.policy.lock").read_text().splitlines():
            if "==" in line and not line.startswith("#"):
                package, release = line.split("==", 1)
                pinned[package.lower().replace("_", "-")] = release
        for package in ("tensorflow", "tensorflow-probability", "tf-keras", "protobuf"):
            if version(package) != pinned[package]:
                raise ValueError(f"Published flight inference runtime differs from lock: {package}")
        import tensorflow as tf
        from tensorflow_probability import distributions as tfd
        from tensorflow.python.framework import type_spec_registry
        from simulation.body_download import download
        download(verify_only=True)
        # TFP renamed the registry key after the published TF2.8 SavedModel.
        # Alias its legacy name to the registered same Independent TypeSpec.
        # SavedModel weights and graph functions are not edited or retrained.
        _ = tfd.Independent
        self.compatibility_alias = {
            "old": "tensorflow_probability.python.distributions.independent.Independent_ACTTypeSpec",
            "new": "tfp.distributions.Independent_ACTTypeSpec"}
        type_spec_registry._NAME_TO_TYPE_SPEC[self.compatibility_alias["old"]] = (
            type_spec_registry.lookup(self.compatibility_alias["new"]))
        self.tf = tf
        self.action_spec = action_spec
        self.model = tf.saved_model.load(str(ROOT / ".runtime/body-published-data/flight"))

    def __call__(self, observation):
        import numpy as np
        from flybody.tasks.task_utils import canonical2real
        batched = self.tf.nest.map_structure(
            lambda value: self.tf.convert_to_tensor(value[None, ...], dtype=self.tf.float32), observation)
        canonical_action = self.model(batched).mean()[0, :].numpy()
        if canonical_action.shape != self.action_spec.shape or not np.isfinite(canonical_action).all():
            raise ValueError("Published policy returned invalid action shape/value")
        return canonical2real(canonical_action, self.action_spec, clip=True)

    def provenance(self) -> dict:
        manifest_path = ROOT / "data/body/published_assets_manifest.json"
        return {"source": "https://doi.org/10.25378/janelia.25309105",
                "trained_policy": "authors' published flight SavedModel, deterministic distribution mean",
                "new_training_performed": False,
                "versions": {p: version(p) for p in ("tensorflow", "tensorflow-probability", "tf-keras", "protobuf")},
                "compatibility_adjustment": self.compatibility_alias,
                "input_conversion": "float32 with one batch dimension",
                "action_conversion": "author canonical2real clipping [-1,1] to real action bounds",
                "asset_manifest_sha256": sha256(manifest_path),
                "flight_saved_model_sha256": json.loads(manifest_path.read_text())["flight_saved_model_sha256"],
                "body_controller_feedback": True, "neural_sensor_feedback": False}
