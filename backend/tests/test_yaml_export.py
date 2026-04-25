import yaml
import pytest
from pathlib import Path

from app.storage.yaml_export import export_official_question, export_generated_question


EXTRACT = {
    "question_text": "Which choice completes the text?",
    "passage_text": "The student _____ the exam.",
    "correct_option_label": "A",
    "options": [
        {"label": "A", "text": "passed"},
        {"label": "B", "text": "pass"},
        {"label": "C", "text": "passing"},
        {"label": "D", "text": "to pass"},
    ],
}
ANNOTATE = {
    "grammar_focus_key": "subject_verb_agreement",
    "grammar_role_key": "error_identification",
    "explanation_short": "Singular subject needs singular verb.",
    "explanation_full": "Long explanation here.",
    "annotation_confidence": 0.95,
    "needs_human_review": False,
}


def test_export_official_creates_file(tmp_path):
    export_official_question(
        question_id="qid-001",
        exam_code="PT01",
        module_code="S1M1",
        question_number=1,
        extract_json=EXTRACT,
        annotate_json=ANNOTATE,
        base_dir=str(tmp_path),
    )
    path = tmp_path / "official" / "PT01_S1M1.yaml"
    assert path.exists()
    data = yaml.safe_load(path.read_text())
    assert data["exam_code"] == "PT01"
    assert data["module_code"] == "S1M1"
    assert len(data["questions"]) == 1
    q = data["questions"][0]
    assert q["question_number"] == 1
    assert q["question_id"] == "qid-001"
    assert q["correct_option_label"] == "A"
    assert q["annotation"]["grammar_focus_key"] == "subject_verb_agreement"


def test_export_official_upserts_by_question_number(tmp_path):
    for i, qid in enumerate(["qid-001", "qid-002", "qid-003"], start=1):
        export_official_question(
            question_id=qid,
            exam_code="PT01",
            module_code="S1M1",
            question_number=i,
            extract_json={**EXTRACT, "question_text": f"Question {i}"},
            annotate_json=ANNOTATE,
            base_dir=str(tmp_path),
        )
    data = yaml.safe_load((tmp_path / "official" / "PT01_S1M1.yaml").read_text())
    assert len(data["questions"]) == 3
    assert [q["question_number"] for q in data["questions"]] == [1, 2, 3]


def test_export_official_overwrites_same_question_number(tmp_path):
    export_official_question(
        question_id="qid-old",
        exam_code="PT01",
        module_code="S1M1",
        question_number=5,
        extract_json={**EXTRACT, "question_text": "Old text"},
        annotate_json=ANNOTATE,
        base_dir=str(tmp_path),
    )
    export_official_question(
        question_id="qid-new",
        exam_code="PT01",
        module_code="S1M1",
        question_number=5,
        extract_json={**EXTRACT, "question_text": "Updated text"},
        annotate_json=ANNOTATE,
        base_dir=str(tmp_path),
    )
    data = yaml.safe_load((tmp_path / "official" / "PT01_S1M1.yaml").read_text())
    assert len(data["questions"]) == 1
    assert data["questions"][0]["question_id"] == "qid-new"
    assert data["questions"][0]["question_text"] == "Updated text"


def test_export_official_separate_modules_separate_files(tmp_path):
    export_official_question("q1", "PT02", "S1M1", 1, EXTRACT, ANNOTATE, base_dir=str(tmp_path))
    export_official_question("q2", "PT02", "S1M2", 1, EXTRACT, ANNOTATE, base_dir=str(tmp_path))
    files = list((tmp_path / "official").iterdir())
    assert len(files) == 2
    names = {f.name for f in files}
    assert names == {"PT02_S1M1.yaml", "PT02_S1M2.yaml"}


def test_export_official_with_section_code_in_filename(tmp_path):
    export_official_question(
        question_id="qid-sec",
        exam_code="PT01",
        module_code="M1",
        question_number=2,
        extract_json=EXTRACT,
        annotate_json=ANNOTATE,
        section_code="S1",
        base_dir=str(tmp_path),
    )
    path = tmp_path / "official" / "PT01_S1_M1.yaml"
    assert path.exists()
    data = yaml.safe_load(path.read_text())
    assert data["exam_code"] == "PT01"
    assert data["section_code"] == "S1"
    assert data["module_code"] == "M1"


def test_export_official_no_passage_omits_key(tmp_path):
    export_official_question(
        question_id="qid-no-passage",
        exam_code="PT01",
        module_code="S2M1",
        question_number=3,
        extract_json={**EXTRACT, "passage_text": None},
        annotate_json=ANNOTATE,
        base_dir=str(tmp_path),
    )
    data = yaml.safe_load((tmp_path / "official" / "PT01_S2M1.yaml").read_text())
    assert "passage_text" not in data["questions"][0]


def test_export_generated_creates_standalone_file(tmp_path):
    export_generated_question(
        question_id="gen-abc123",
        extract_json=EXTRACT,
        annotate_json=ANNOTATE,
        generation_source_set={"grammar_focus": "subject_verb_agreement"},
        base_dir=str(tmp_path),
    )
    path = tmp_path / "generated" / "gen-abc123.yaml"
    assert path.exists()
    data = yaml.safe_load(path.read_text())
    assert data["question_id"] == "gen-abc123"
    assert data["annotation"]["explanation_short"] == "Singular subject needs singular verb."
    assert data["generation_source_set"]["grammar_focus"] == "subject_verb_agreement"


def test_export_generated_no_source_set(tmp_path):
    export_generated_question(
        question_id="gen-xyz",
        extract_json=EXTRACT,
        annotate_json=ANNOTATE,
        base_dir=str(tmp_path),
    )
    data = yaml.safe_load((tmp_path / "generated" / "gen-xyz.yaml").read_text())
    assert "generation_source_set" not in data


def test_export_official_is_nonfatal_on_bad_path(tmp_path):
    # Should not raise even if directory can't be created (read-only simulation via bad path)
    export_official_question(
        question_id="qid",
        exam_code="PT01",
        module_code="S1M1",
        question_number=1,
        extract_json=EXTRACT,
        annotate_json=ANNOTATE,
        base_dir="/dev/null/impossible",  # can't create dirs here
    )  # must not raise
