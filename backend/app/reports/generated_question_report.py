"""Render a generated question's stored lineage, annotation, options, generator
self-check and review-swarm output as a single Markdown audit report.

Pure function over the dict shape produced by
``app.routers.admin._serialize_generated_candidates`` — no DB access, so it is
unit-testable and the same renderer can back an API endpoint or a CLI dump.
The layout mirrors the hand-written ``sample_questions_claude.md`` walkthrough:
profile → passage → stem → options → template → self-check → review.
"""
from __future__ import annotations

import json
import re
from typing import Any

# Annotation keys shown in the Template table, in display order. Keys absent or
# empty on a given question are skipped, so one list serves both domains.
_TEMPLATE_KEYS: tuple[str, ...] = (
    "question_family_key",
    "grammar_role_key",
    "grammar_focus_key",
    "syntactic_trap_key",
    "syntactic_trap_intensity",
    "secondary_grammar_focus_keys",
    "reading_skill_family_key",
    "skill_family_key",
    "reading_focus_key",
    "target_test_construct_key",
    "target_craft_subconstruct_key",
    "answer_mechanism_key",
    "solver_pattern_key",
    "evidence_scope_key",
    "evidence_location_key",
    "reasoning_trap_key",
    "passage_structure_pattern",
    "passage_architecture_key",
    "inference_type_note",
    "text_relationship_key",
    "stem_type_key",
    "stimulus_mode_key",
    "disambiguation_rule_applied",
    "difficulty_overall",
    "difficulty_grammar",
    "difficulty_reading",
    "difficulty_inference",
    "difficulty_vocab",
    "distractor_strength",
    "topic_broad",
    "topic_fine",
    "evidence_span_text",
)

# Reviewer score keys in rubric order; any extra keys a reviewer emits follow.
_SCORE_KEYS: tuple[str, ...] = (
    "realism_score",
    "sat_fidelity_score",
    "difficulty_match_score",
    "distractor_quality_score",
    "taxonomy_match_score",
    "explanation_quality_score",
    "copy_risk_score",
)


def _cell(value: Any) -> str:
    """Make a value safe inside a Markdown table cell."""
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        text = ", ".join(str(v) for v in value) if value else "—"
    elif isinstance(value, dict):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = str(value)
    return text.replace("|", "\\|").replace("\n", " ").strip() or "—"


def _json_block(value: Any) -> str:
    return "```json\n" + json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n```"


def _passage_stats(text: str | None) -> str:
    if not text:
        return "no passage"
    words = len(text.split())
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]
    lengths = " / ".join(str(len(s.split())) for s in sentences)
    return f"{words} words / {len(sentences)} sentences (lengths {lengths})"


def _source_label(src: dict[str, Any]) -> str:
    parts = [
        src.get("source_test_name") or src.get("source_exam_code"),
        src.get("source_module_code") and f"Mod {src['source_module_code']}",
        src.get("source_question_number") is not None and f"Q{src['source_question_number']}",
    ]
    label = " · ".join(str(p) for p in parts if p)
    return label or "(official question)"


def render_generated_question_report(item: dict[str, Any]) -> str:
    """Return a Markdown report for one serialized generated-question item."""
    ann: dict[str, Any] = item.get("annotation") or {}
    job: dict[str, Any] = item.get("job") or {}
    batch: dict[str, Any] = item.get("batch") or {}
    consensus: dict[str, Any] | None = item.get("consensus")
    reviews: list[dict[str, Any]] = item.get("review_results") or []
    options: list[dict[str, Any]] = item.get("options") or []
    profile = item.get("generation_profile")
    self_check = item.get("self_check")
    source_set = item.get("generation_source_set") or {}

    domain = item.get("domain") or "unknown"
    if domain == "grammar":
        focus = f"{ann.get('grammar_role_key', '?')} · {ann.get('grammar_focus_key', '?')}"
    else:
        focus = f"{ann.get('reading_skill_family_key') or ann.get('skill_family_key', '?')} · {ann.get('reading_focus_key', '?')}"
    difficulty = ann.get("difficulty_overall") or source_set.get("difficulty_overall") or "?"

    out: list[str] = []
    out.append(f"# Generated Question Report — {domain} · {focus} · {difficulty}")
    out.append("")
    out.append(f"- **question_id:** `{item.get('id')}`")
    out.append(f"- **practice_status:** {item.get('practice_status')} · **overlap:** {item.get('official_overlap_status')}")
    if job:
        out.append(f"- **generator:** {job.get('provider_name')} / {job.get('model_name')} · job {job.get('status')} · `{job.get('id')}`")
    if batch:
        out.append(f"- **batch:** `{batch.get('id')}` · {batch.get('status')} · policy {batch.get('release_policy')}")
    if item.get("created_at"):
        out.append(f"- **created:** {item['created_at']}")
    if item.get("rejection_reason"):
        out.append(f"- **rejected:** {item['rejection_reason']}")

    # --- Lineage ---------------------------------------------------------
    out.append("")
    out.append("## Lineage")
    out.append("")
    derived = item.get("derived_from_question_id")
    if derived:
        out.append(f"- **derived_from_question_id:** `{derived}`")
    sources = item.get("source_examples") or []
    if sources:
        out.append("- **source examples (calibration):**")
        for src in sources:
            snippet = (src.get("question_text") or "").strip()
            snippet = (snippet[:90] + "…") if len(snippet) > 90 else snippet
            out.append(f"  - `{src.get('id')}` — {_source_label(src)}" + (f" — {snippet}" if snippet else ""))
    else:
        out.append("- no source examples recorded")
    spec = {k: v for k, v in source_set.items() if k != "source_question_ids" and v not in (None, "", [])}
    if spec:
        out.append("")
        out.append("**Generation request (target spec):**")
        out.append("")
        out.append(_json_block(spec))

    # --- Phase 1 ---------------------------------------------------------
    out.append("")
    out.append("## Phase 1 — generation_profile")
    out.append("")
    out.append(_json_block(profile) if profile else "_no generation_profile stored_")

    # --- Phase 2 / 3 -----------------------------------------------------
    out.append("")
    out.append(f"## Phase 2 — Passage ({_passage_stats(item.get('passage_text'))})")
    out.append("")
    passage = item.get("passage_text")
    if passage:
        out.append("> " + passage.strip().replace("\n", "\n> "))
    else:
        out.append("_no passage_")
    if item.get("paired_passage_text"):
        out.append("")
        out.append("**Paired passage:**")
        out.append("")
        out.append("> " + item["paired_passage_text"].strip().replace("\n", "\n> "))
    if item.get("underlined_text"):
        out.append("")
        out.append(f"**underlined_text:** {item['underlined_text']}")
    out.append("")
    out.append("## Phase 3 — Stem")
    out.append("")
    out.append(f"**{(item.get('question_text') or '').strip()}**")

    # --- Phase 4 ---------------------------------------------------------
    out.append("")
    out.append("## Phase 4 — Options")
    out.append("")
    out.append("| | Option | distractor_type_key | plausibility_source_key | student_failure_mode_key | precision | why_wrong |")
    out.append("|---|---|---|---|---|---|---|")
    correct = item.get("correct_option_label")
    for opt in options:
        label = opt.get("label") or opt.get("option_label")
        mark = f"**{label} ✅**" if label == correct or opt.get("is_correct") else str(label)
        out.append(
            f"| {mark} | {_cell(opt.get('text') or opt.get('option_text'))} | "
            f"{_cell(opt.get('distractor_type_key'))} | {_cell(opt.get('plausibility_source_key'))} | "
            f"{_cell(opt.get('student_failure_mode_key'))} | {_cell(opt.get('precision_score'))} | "
            f"{_cell(opt.get('why_wrong') or opt.get('why_plausible'))} |"
        )
    if not options:
        out.append("| — | _no options stored_ | | | | | |")

    # --- Template --------------------------------------------------------
    out.append("")
    out.append("## Template (annotation)")
    out.append("")
    out.append("| Field | Value |")
    out.append("|---|---|")
    for key in _TEMPLATE_KEYS:
        value = ann.get(key)
        if value in (None, "", [], {}):
            continue
        out.append(f"| {key} | {_cell(value)} |")
    conf = ann.get("annotation_confidence")
    if conf is not None:
        out.append(f"| annotation_confidence | {_cell(conf)} |")
    if ann.get("needs_human_review") is not None:
        out.append(f"| needs_human_review | {_cell(ann.get('needs_human_review'))} |")

    explanation = (item.get("annotation_explanation") or {}).get("explanation_full") or item.get("explanation_text")
    if explanation:
        out.append("")
        out.append("## Explanation")
        out.append("")
        out.append(explanation.strip())

    # --- Phase 5 ---------------------------------------------------------
    out.append("")
    out.append("## Phase 5 — Generator self-check")
    out.append("")
    if isinstance(self_check, dict) and self_check:
        for key, value in self_check.items():
            out.append(f"- **{key}:** {_cell(value)}")
    else:
        out.append("_no self_check emitted (generated before the phase-based prompt, or the model omitted it)_")

    # --- Review swarm ----------------------------------------------------
    out.append("")
    out.append("## Review swarm")
    out.append("")
    if reviews:
        score_keys = list(_SCORE_KEYS) + sorted(
            {k for r in reviews for k in (r.get("scores_jsonb") or {}) if k not in _SCORE_KEYS}
        )
        header = "| Reviewer | " + " | ".join(k.replace("_score", "") for k in score_keys) + " | verdict | notes |"
        out.append(header)
        out.append("|" + "---|" * (len(score_keys) + 3))
        for r in reviews:
            scores = r.get("scores_jsonb") or {}
            cells = " | ".join(_cell(scores.get(k)) for k in score_keys)
            notes = r.get("review_notes") or r.get("error_message") or ""
            out.append(
                f"| {r.get('provider_name')}/{r.get('model_name')} | {cells} | "
                f"{_cell(r.get('verdict'))} ({_cell(r.get('review_status'))}) | {_cell(notes)} |"
            )
    else:
        out.append("_no reviewer results yet_")
    if consensus:
        out.append("")
        out.append(f"**Consensus:** `{consensus.get('consensus_verdict')}` — "
                   f"{consensus.get('reviewer_count')} reviewer(s); votes accept/needs_review/reject = "
                   f"{consensus.get('accept_votes')}/{consensus.get('needs_review_votes')}/{consensus.get('reject_votes')}; "
                   f"disagreement {_cell(consensus.get('reviewer_disagreement'))}"
                   + (" ⚠ high" if consensus.get("high_disagreement_flag") else ""))
        averages = {
            k: consensus.get(k)
            for k in (
                "average_realism", "average_sat_fidelity", "average_difficulty_match",
                "average_distractor_quality", "average_taxonomy_match", "max_copy_risk",
            )
            if consensus.get(k) is not None
        }
        if averages:
            out.append("")
            out.append("| " + " | ".join(k.replace("average_", "avg ") for k in averages) + " |")
            out.append("|" + "---|" * len(averages))
            out.append("| " + " | ".join(_cell(v) for v in averages.values()) + " |")
        reasons = consensus.get("reasons_jsonb")
        if reasons:
            out.append("")
            out.append("**Consensus reasons:**")
            out.append("")
            out.append(_json_block(reasons))

    # --- Validation ------------------------------------------------------
    errors = job.get("validation_errors_jsonb") or []
    if errors:
        out.append("")
        out.append("## Validation notes")
        out.append("")
        for err in errors:
            if isinstance(err, dict):
                out.append(f"- **{err.get('severity', 'note')}** `{err.get('field', '')}` — {err.get('message', '')}")
            else:
                out.append(f"- {err}")

    out.append("")
    return "\n".join(out)
