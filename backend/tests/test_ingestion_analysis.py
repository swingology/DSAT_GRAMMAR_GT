"""Tests for ingestion analysis reports and re-appraisal creation."""
from __future__ import annotations

import json
from types import SimpleNamespace

from app.pipeline import ingestion_analysis


def _repo(tmp_path):
    (tmp_path / "vocabulary").mkdir()
    (tmp_path / "backend" / "app" / "models").mkdir(parents=True)
    (tmp_path / "vocabulary" / "master.json").write_text('{"schema_version":1}\n')
    (tmp_path / "rules_agent_dsat_reading_v2.md").write_text("reading rules\n")
    (tmp_path / "rules_agent_dsat_grammar_ingestion_generation_v7.md").write_text("grammar rules\n")
    (tmp_path / "backend" / "app" / "models" / "ontology.py").write_text("KEYS = ()\n")
    return tmp_path


def _job(**overrides):
    data = {
        "id": "job-1",
        "content_origin": "official",
        "status": "needs_review",
        "pass1_json": {"source_exam_code": "PT04"},
        "pass2_json": {
            "_annotations": [
                {
                    "source_question_number": 1,
                    "annotation": {
                        "source_question_number": 1,
                        "question_text": "Question one?",
                        "question_family_key": "information_and_ideas",
                        "skill_family_key": "command_of_evidence_textual",
                        "reading_focus_key": "evidence_supports_claim",
                    },
                }
            ],
            "_amendment_proposals": [{"proposed_value": "new_key"}],
        },
        "validation_errors_jsonb": [{"field": "x", "message": "bad"}],
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_write_ingestion_analysis_creates_expected_report_layout(tmp_path):
    repo = _repo(tmp_path)

    report_dir = ingestion_analysis.write_ingestion_analysis(_job(), repo_root=repo)

    assert report_dir is not None
    assert report_dir.parent.name == "PT04"
    assert (report_dir / "summary.md").exists()
    assert (report_dir / "taxonomy_coverage.json").exists()
    assert (report_dir / "validation_failures.json").exists()
    assert (report_dir / "amendment_candidates.json").exists()
    assert (report_dir / "questions" / "q001.md").exists()
    coverage = json.loads((report_dir / "taxonomy_coverage.json").read_text())
    assert coverage["hashes"]["master_json_hash"]
    assert coverage["field_counts"]["reading_focus_key"]["evidence_supports_claim"] == 1


def test_write_ingestion_analysis_skips_non_official_jobs(tmp_path):
    repo = _repo(tmp_path)

    assert ingestion_analysis.write_ingestion_analysis(_job(content_origin="generated"), repo_root=repo) is None


def test_write_reappraisals_after_master_hash_changes(tmp_path):
    repo = _repo(tmp_path)
    report_dir = ingestion_analysis.write_ingestion_analysis(_job(), repo_root=repo)
    old_hash = json.loads((report_dir / "taxonomy_coverage.json").read_text())["hashes"]["master_json_hash"]
    (repo / "vocabulary" / "master.json").write_text('{"schema_version":2}\n')
    new_hash = ingestion_analysis.current_analysis_hashes(repo_root=repo)["master_json_hash"]

    written = ingestion_analysis.write_reappraisals_for_master_growth(repo_root=repo)

    assert old_hash != new_hash
    assert len(written) == 1
    assert written[0].name == f"reappraisal_{new_hash[:12]}.md"
    assert old_hash in written[0].read_text()


def test_reappraisal_markdown_records_exam_and_hash_comparison(tmp_path):
    """Re-appraisal content carries both hashes and the source exam/count."""
    repo = _repo(tmp_path)
    ingestion_analysis.write_ingestion_analysis(_job(), repo_root=repo)
    (repo / "vocabulary" / "master.json").write_text('{"schema_version":2}\n')
    new_hash = ingestion_analysis.current_analysis_hashes(repo_root=repo)["master_json_hash"]

    written = ingestion_analysis.write_reappraisals_for_master_growth(repo_root=repo)

    text = written[0].read_text()
    assert "current_master_json_hash" in text
    assert new_hash in text
    assert "source_exam_code: `PT04`" in text
    assert "question_count: `1`" in text


def test_question_records_falls_back_to_pass1_questions():
    """pass2_json is None -> records come from pass1_json['questions']."""
    job = _job(
        pass2_json=None,
        pass1_json={
            "source_exam_code": "PT04",
            "questions": [
                {"source_question_number": 1, "skill_family_key": "inferences"},
            ],
        },
    )
    records = ingestion_analysis._question_records(job)
    assert len(records) == 1
    assert records[0]["skill_family_key"] == "inferences"


def test_question_records_handles_single_question_pass2_without_annotations():
    """A flat single-question pass2_json (no _annotations wrapper) yields one record."""
    job = _job(pass2_json={"source_question_number": 1, "skill_family_key": "inferences"})
    records = ingestion_analysis._question_records(job)
    assert records == [{"source_question_number": 1, "skill_family_key": "inferences"}]


def test_question_records_handles_empty_annotations_list():
    """An empty _annotations list yields no records."""
    job = _job(pass2_json={"_annotations": []})
    assert ingestion_analysis._question_records(job) == []


def test_empty_question_records_do_not_emit_stub_files(tmp_path):
    """pass1 fallback rows with no content must not produce empty question files."""
    repo = _repo(tmp_path)
    job = _job(
        pass2_json=None,
        pass1_json={"source_exam_code": "PT04", "questions": [{"page": 3}]},
    )
    report_dir = ingestion_analysis.write_ingestion_analysis(job, repo_root=repo)
    assert list((report_dir / "questions").glob("*.md")) == []


def test_amendment_candidates_captures_legacy_top_level_proposal(tmp_path):
    """A legacy top-level amendment_proposal key is captured via the shared extractor."""
    repo = _repo(tmp_path)
    job = _job(
        pass2_json={
            "source_question_number": 1,
            "amendment_proposal": {"proposed_value": "legacy_key"},
        }
    )
    report_dir = ingestion_analysis.write_ingestion_analysis(job, repo_root=repo)
    candidates = json.loads((report_dir / "amendment_candidates.json").read_text())
    assert candidates["amendment_candidates"] == [{"proposed_value": "legacy_key"}]
