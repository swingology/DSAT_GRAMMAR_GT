"""Resolve questions.skill_key — the College Board skill every verbal question carries.

skill_key is a column, deliberately separate from annotation_jsonb.skill_family_key.
That key stays reading-only because several readers treat its mere presence as "this is
a reading question" (diagnostic.queries.derive_domain, the practice filter, auto-release).

Source, in order of trust:
  cb          questions.cb_skill_key is set -> College Board's own label. Command of
              Evidence is split textual / quantitative by the stem.
  question_text  the question's wording matches a College Board boilerplate stem that maps to
              one skill (>=95% pure over CB's own 1,845 questions). Both the wording and the
              label are College Board's, so this outranks anything an LLM annotated.
  annotation  the annotation already carries a legal reading skill_family_key.
  map         vocabulary/mappings/cb_skill_map.json, deterministic rules only, in order:
              stem_type_key, role/focus, role. Calibrated on LLM-assigned keys.
  manual      set by a person. Never produced here and never overwritten here.

Anyone reading skill_key must derive the domain from the skill (SKILL_FAMILY_BY_QUESTION_FAMILY),
not from derive_domain / question_domain: the annotation's routing domain contradicts the
skill's domain on ~100 official rows.
"""
from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path

from app.models.ontology import READING_SKILL_FAMILY_KEYS, SKILL_FAMILY_KEYS

logger = logging.getLogger(__name__)

# parents[3] is the repo root on the host and / in the container (same as admin._VOCAB_DIR).
MAP_PATH = Path(__file__).resolve().parents[3] / "vocabulary" / "mappings" / "cb_skill_map.json"

# Agreed with existing annotations on 174/174 Command of Evidence rows and leaked on
# 0/144 textual stems (ONTOLOGY_REFACTOR_PLAN.md §1.6, TASK-06).
QUANT_STEM = re.compile(r"\b(graph|table|data in the)\b", re.I)

Rules = tuple[dict[str, str], dict[str, str], dict[str, str], dict[str, str]]


def question_key(text: str | None) -> str:
    """Normalised last sentence. Must match calibration_report.question_key."""
    last = re.split(r"(?<=[.?!])\s+", (text or "").strip())[-1]
    return re.sub(r"[^a-z]+", " ", last.lower()).strip()


@lru_cache(maxsize=1)
def load_rules() -> Rules:
    """(by_question_text, by_stem_type_key, by_role/focus, by_role) — deterministic only."""
    try:
        data = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        # Degrade to cb + annotation sources rather than failing an ingest.
        logger.warning("skill map unavailable at %s (%s); map-sourced skill_key disabled", MAP_PATH, exc)
        return {}, {}, {}, {}

    def pick(rows: list[dict]) -> dict[str, str]:
        return {r["key"]: r["skill_key"] for r in rows
                if r["status"] == "deterministic" and r["skill_key"] in SKILL_FAMILY_KEYS}

    return (pick(data.get("by_question_text", [])), pick(data["by_stem_type_key"]),
            pick(data["by_role_and_focus"]), pick(data["by_role"]))


def resolve_skill_key(
    *,
    cb_skill_key: str | None,
    stem_text: str | None,
    stem_type_key: str | None,
    annotation: dict | None,
    rules: Rules | None = None,
) -> tuple[str | None, str | None]:
    """Return (skill_key, source), or (None, None) when nothing reliable applies."""
    ann = annotation or {}
    if cb_skill_key:
        skill = cb_skill_key
        if skill == "command_of_evidence":
            skill += "_quantitative" if QUANT_STEM.search(stem_text or "") else "_textual"
        return (skill, "cb") if skill in SKILL_FAMILY_KEYS else (None, None)

    by_text, by_stem, by_focus, by_role = rules if rules is not None else load_rules()
    wording = question_key(stem_text)
    if wording in by_text:
        return by_text[wording], "question_text"

    if ann.get("skill_family_key") in READING_SKILL_FAMILY_KEYS:
        return ann["skill_family_key"], "annotation"

    # The annotation's stem_type_key is the canonical one; generated questions never
    # set the questions.stem_type_key column at all.
    stem_type = ann.get("stem_type_key") or stem_type_key
    role, focus = ann.get("grammar_role_key"), ann.get("grammar_focus_key")
    for table, key in ((by_stem, stem_type), (by_focus, f"{role}/{focus}"), (by_role, role)):
        if key in table:
            return table[key], "map"
    return None, None


def apply_skill_key(question, annotation: dict | None) -> None:
    """Set question.skill_key after an annotation is attached (ingest, generate, reannotate).

    Leaves a human label alone, and never replaces an existing value with nothing: a
    reannotation that no longer matches a rule should not erase a label that did.
    """
    if question.skill_key_source == "manual":
        return
    skill, source = resolve_skill_key(
        cb_skill_key=question.cb_skill_key,
        stem_text=question.current_question_text,
        stem_type_key=question.stem_type_key,
        annotation=annotation,
    )
    if skill is not None:
        question.skill_key, question.skill_key_source = skill, source
