"""Tests for the controlled-vocabulary source-of-truth system.

Covers the master.json -> ontology.py generator drift check and the Part B
candidates review queue (non-blocking recording of unknown keys).
"""
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GEN_VOCAB = REPO_ROOT / "scripts" / "gen_vocab.py"


def test_artefacts_in_sync_with_master_json():
    """ontology.py and the rules-doc VOCAB blocks must match master.json.

    This is the CI drift gate: if it fails, run `python scripts/gen_vocab.py
    --generate` and commit the result.
    """
    result = subprocess.run(
        [sys.executable, str(GEN_VOCAB), "--check"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, (
        f"vocabulary drift detected:\n{result.stdout}\n{result.stderr}"
    )


def test_validator_records_unknown_question_key(monkeypatch, tmp_path):
    """An unknown question-level key is flagged AND queued, non-blocking."""
    from app.models import vocab_candidates
    from app.pipeline.validator import validate_question

    queue = tmp_path / "candidates.json"
    monkeypatch.setattr(vocab_candidates, "CANDIDATES_PATH", queue)

    errors = validate_question(
        {"question_text": "x", "options": [], "stem_type_key": "not_a_real_stem"},
        job_id="job-xyz",
    )
    assert any(e["field"] == "stem_type_key" for e in errors)
    assert queue.exists()
    text = queue.read_text()
    assert "not_a_real_stem" in text
    assert "STEM_TYPE_KEYS" in text
    assert "job-xyz" in text


def test_option_unknown_key_is_non_blocking(monkeypatch, tmp_path):
    """OptionAnalysis must accept (not reject) an unknown controlled key."""
    from app.models import vocab_candidates
    from app.models.options import OptionAnalysis

    monkeypatch.setattr(vocab_candidates, "CANDIDATES_PATH",
                         tmp_path / "candidates.json")

    opt = OptionAnalysis(
        option_label="A", option_text="t", is_correct=False,
        option_role="distractor", student_failure_mode_key="hallucinated_mode",
    )
    assert opt.student_failure_mode_key == "hallucinated_mode"


def test_option_distractor_distance_still_blocks():
    """distractor_distance is a fixed micro-enum — unknown values still raise."""
    from app.models.options import OptionAnalysis

    with pytest.raises(ValueError):
        OptionAnalysis(
            option_label="A", option_text="t", is_correct=True,
            option_role="correct", distractor_distance="enormous",
        )


def test_candidate_dedup_increments_occurrences(monkeypatch, tmp_path):
    """Recording the same key twice merges into one row with occurrences=2."""
    from app.models import vocab_candidates

    queue = tmp_path / "candidates.json"
    monkeypatch.setattr(vocab_candidates, "CANDIDATES_PATH", queue)

    vocab_candidates.record_candidate("STEM_TYPE_KEYS", "dup_key", job_id="j1")
    vocab_candidates.record_candidate("STEM_TYPE_KEYS", "dup_key", job_id="j2")

    import json
    rows = json.loads(queue.read_text())["candidates"]
    assert len(rows) == 1
    assert rows[0]["occurrences"] == 2
    assert set(rows[0]["job_ids"]) == {"j1", "j2"}
