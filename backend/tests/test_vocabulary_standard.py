"""Baseline integrity and collision guard, without provider or database calls."""
import hashlib
import json
from pathlib import Path
import runpy
import shutil


def test_standard_rejects_unknown_target_and_unrecorded_drift(tmp_path):
    root = Path(__file__).resolve().parents[2]
    module = runpy.run_path(str(root / "chatgpt_refactor_rules/verify_standard.py"))
    assert module["verify"]() == []
    release = tmp_path / "release"
    shutil.copytree(module["RELEASE"], release)
    crosswalk = release / "crosswalk.json"
    data = json.loads(crosswalk.read_text())
    data["mappings"][0]["official_targets"] = ["cb.not_a_real_skill"]
    crosswalk.write_text(json.dumps(data))
    problems = module["verify"](root, release)
    assert any("Drift in release_files: crosswalk.json" in p for p in problems)
    # Even if a hash is refreshed, an invalid official target must still fail.
    lock_path = release / "baseline.lock.json"
    lock = json.loads(lock_path.read_text())
    lock["release_files"]["crosswalk.json"] = hashlib.sha256(crosswalk.read_bytes()).hexdigest()
    lock_path.write_text(json.dumps(lock))
    assert any("Unknown official target" in p for p in module["verify"](root, release))
