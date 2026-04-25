"""YAML export for persisted questions.

Official questions are grouped into one file per exam+module combination:
  archive/official/{exam_code}_{module_code}.yaml

Generated questions each get their own file:
  archive/generated/{question_id}.yaml

Each write is idempotent: re-ingesting the same question_number upserts it in place.
Export failures are non-fatal — a log message is emitted but the pipeline continues.
"""
import logging
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

_ANNOTATION_KEYS = [
    "grammar_focus_key",
    "grammar_role_key",
    "stimulus_mode_key",
    "stem_type_key",
    "explanation_short",
    "explanation_full",
    "annotation_confidence",
    "needs_human_review",
]


def _build_question_record(
    question_id: str,
    extract_json: dict,
    annotate_json: dict,
    question_number: Optional[int] = None,
) -> dict:
    record: dict = {}
    if question_number is not None:
        record["question_number"] = question_number
    record["question_id"] = question_id
    record["question_text"] = extract_json.get("question_text", "")
    if extract_json.get("passage_text"):
        record["passage_text"] = extract_json["passage_text"]
    record["correct_option_label"] = extract_json.get("correct_option_label", "")
    record["options"] = extract_json.get("options", [])
    annotation = {k: annotate_json[k] for k in _ANNOTATION_KEYS if k in annotate_json}
    if annotation:
        record["annotation"] = annotation
    return record


def export_official_question(
    question_id: str,
    exam_code: str,
    module_code: str,
    question_number: Optional[int],
    extract_json: dict,
    annotate_json: dict,
    section_code: Optional[str] = None,
    base_dir: str = "./archive",
) -> None:
    """Upsert one question into the shared per-module YAML file.

    Filename: {exam_code}_{section_code}_{module_code}.yaml when section_code is
    present, otherwise {exam_code}_{module_code}.yaml.
    """
    parts = [exam_code]
    if section_code:
        parts.append(section_code)
    parts.append(module_code)
    filename = "_".join(parts) + ".yaml"
    path = Path(base_dir) / "official" / filename
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        existing: dict = {}
        if path.exists():
            with open(path, encoding="utf-8") as f:
                existing = yaml.safe_load(f) or {}

        by_number: dict = {
            q["question_number"]: q
            for q in existing.get("questions", [])
            if "question_number" in q
        }
        record = _build_question_record(question_id, extract_json, annotate_json, question_number)
        key = question_number if question_number is not None else question_id
        by_number[key] = record

        header: dict = {"exam_code": exam_code}
        if section_code:
            header["section_code"] = section_code
        header["module_code"] = module_code
        data = {
            **header,
            "questions": sorted(
                by_number.values(),
                key=lambda q: q.get("question_number") or 0,
            ),
        }
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    except Exception:
        logger.exception("Failed to export official question %s to %s", question_id, path)



def export_generated_question(
    question_id: str,
    extract_json: dict,
    annotate_json: dict,
    generation_source_set: Optional[dict] = None,
    base_dir: str = "./archive",
) -> None:
    """Write a standalone YAML for a generated question."""
    path = Path(base_dir) / "generated" / f"{question_id}.yaml"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        record = _build_question_record(question_id, extract_json, annotate_json)
        if generation_source_set:
            record["generation_source_set"] = generation_source_set
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(record, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    except Exception:
        logger.exception("Failed to export generated question %s to %s", question_id, path)
