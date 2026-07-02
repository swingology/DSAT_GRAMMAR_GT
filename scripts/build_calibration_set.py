#!/usr/bin/env python3
"""
Build the 50-question calibration set from official DSAT questions in the DB.

Outputs:
  analysis/calibration/official_classifications.json   — all official questions with metadata
  analysis/calibration/calibration_set.json            — selected 20 grammar + 20 reading + flags
  analysis/calibration/calibration_report.md           — human-readable summary

Calibration plan (from TASKS_GENERATION.md):
  20 grammar questions with varied focus keys
  20 reading questions with varied skill families
  10 weak/negative controls (flagged here, must be generated separately)
"""

import json
import os
import sys
import psycopg2
import psycopg2.extras
from collections import defaultdict
from datetime import datetime

DB_DSN = "postgresql://dsat:dsat_dev@localhost:5437/dsat_dev"

# ── Approved taxonomy from rules_agent_dsat_grammar_ingestion_generation_v7.md ──

VALID_GRAMMAR_FOCUS_KEYS = {
    # D.2.1 sentence boundary
    "sentence_fragment", "comma_splice", "run_on_sentence", "sentence_boundary",
    # D.2.2 agreement
    "subject_verb_agreement", "pronoun_antecedent_agreement",
    "noun_countability", "determiners_articles", "affirmative_agreement",
    # D.2.3 pronoun
    "pronoun_case", "pronoun_clarity",
    # D.2.4 verb form
    "verb_tense_consistency", "verb_form", "voice_active_passive", "negation",
    # D.2.5 modifier
    "modifier_placement", "comparative_structures", "illogical_comparison",
    "adjective_adverb_distinction", "logical_predication", "relative_pronouns",
    # D.2.6 punctuation
    "punctuation_comma", "colon_dash_use", "semicolon_use",
    "conjunctive_adverb_usage", "apostrophe_use", "possessive_contraction",
    "appositive_punctuation", "hyphen_usage", "quotation_punctuation",
    "unnecessary_internal_punctuation", "end_punctuation_question_statement",
    # D.2.7 parallel
    "parallel_structure", "elliptical_constructions", "conjunction_usage",
    # D.2.8 expression of ideas
    "redundancy_concision", "precision_word_choice", "register_style_consistency",
    "logical_relationships", "emphasis_meaning_shifts", "data_interpretation_claims",
    "transition_logic", "commonly_confused_words", "preposition_idiom",
}

VALID_SKILL_FAMILY_KEYS_GRAMMAR = {
    "Boundaries", "boundaries",
    "Form, Structure, and Sense", "form_structure_and_sense",
    "Expression of Ideas", "expression_of_ideas",
    "agreement",  # legacy
}

VALID_READING_SKILL_FAMILY_KEYS = {
    "words_in_context", "Words in Context",
    "text_structure_and_purpose", "Text Structure and Purpose",
    "cross_text_connections", "Cross-Text Connections",
    "central_ideas_and_details", "Central Ideas and Details",
    "command_of_evidence", "Command of Evidence",
    "inferences", "Inferences",
    "rhetorical_synthesis", "Rhetorical Synthesis",
}

VALID_DOMAINS = {
    "Standard English Conventions",
    "Expression of Ideas",
    "Craft and Structure",
    "Information and Ideas",
}

# Grammar focus keys that are strong calibration candidates
# (high frequency on real SAT, clear correct/wrong structure)
PRIORITY_GRAMMAR_KEYS = [
    "subject_verb_agreement",
    "verb_tense_consistency",
    "transition_logic",
    "punctuation_comma",
    "sentence_boundary",
    "comma_splice",
    "appositive_punctuation",
    "semicolon_use",
    "unnecessary_internal_punctuation",
    "pronoun_antecedent_agreement",
    "verb_form",
    "logical_predication",
    "end_punctuation_question_statement",
    "colon_dash_use",
    "logical_relationships",
    "possessive_contraction",
    "modifier_placement",
    "relative_pronouns",
    "parallel_structure",
    "register_style_consistency",
]

PRIORITY_READING_KEYS = [
    "words_in_context",
    "central_ideas_and_details",
    "text_structure_and_purpose",
    "inferences",
    "command_of_evidence",
    "rhetorical_synthesis",
    "cross_text_connections",
]


def normalize_skill_family(domain: str, sfk: str | None, gfk: str | None) -> str:
    """Return a normalized skill_family_key for consistent grouping."""
    if not sfk:
        return sfk or "unknown"
    sfk_lower = sfk.lower().replace(",", "").replace(" ", "_")
    return sfk_lower


def classify_question(row: dict) -> dict:
    """
    Validate and classify a single question row.
    Returns a classification dict with quality flags.
    """
    ann = row["annotation_jsonb"] or {}
    nested = ann.get("classification") or {}
    # Some annotations store keys flat at the top level; others nest under "classification"
    domain = ann.get("domain") or nested.get("domain") or ""
    sfk = ann.get("skill_family_key") or nested.get("skill_family_key") or ann.get("skill_family") or nested.get("skill_family") or ""
    gfk = ann.get("grammar_focus_key") or nested.get("grammar_focus_key") or ""
    rfk = ann.get("reading_focus_key") or nested.get("reading_focus_key") or ""
    difficulty = ann.get("difficulty_overall") or nested.get("difficulty_overall") or ""
    stem_type = ann.get("stem_type_key") or nested.get("stem_type_key") or row.get("stem_type_key") or ""
    stimulus = ann.get("stimulus_mode_key") or nested.get("stimulus_mode_key") or row.get("stimulus_mode_key") or ""

    flags = []
    is_grammar = domain == "Standard English Conventions"
    is_reading = domain in ("Craft and Structure", "Information and Ideas", "Expression of Ideas")

    # Validate grammar_focus_key
    gfk_valid = (not gfk) or (gfk in VALID_GRAMMAR_FOCUS_KEYS)
    if gfk and not gfk_valid:
        flags.append(f"non_standard_grammar_focus_key:{gfk}")

    # Validate domain
    if domain and domain not in VALID_DOMAINS:
        flags.append(f"non_standard_domain:{domain}")

    # Missing domain
    if not domain:
        flags.append("missing_domain")

    # Missing difficulty
    if not difficulty:
        flags.append("missing_difficulty")

    # Missing grammar_focus_key for SEC questions
    if is_grammar and not gfk:
        flags.append("missing_grammar_focus_key")

    # Non-standard skill_family_key casing (mixed case is inconsistent)
    if sfk and sfk not in ("Boundaries", "Form, Structure, and Sense", "Expression of Ideas",
                           "Agreement") and sfk not in VALID_READING_SKILL_FAMILY_KEYS:
        if sfk.lower() in {s.lower() for s in VALID_SKILL_FAMILY_KEYS_GRAMMAR | VALID_READING_SKILL_FAMILY_KEYS}:
            flags.append(f"inconsistent_skill_family_casing:{sfk}")

    # Build the output classification record
    options_raw = ann.get("options") or []
    options_out = []
    for opt in options_raw:
        options_out.append({
            "label": opt.get("option_label"),
            "text": opt.get("option_text"),
            "is_correct": opt.get("is_correct"),
            "role": opt.get("option_role"),
            "distractor_type": opt.get("distractor_type_key"),
            "student_failure_mode": opt.get("student_failure_mode_key"),
            "why_wrong": opt.get("why_wrong"),
            "why_plausible": opt.get("why_plausible"),
        })

    gen_profile = ann.get("generation_profile") or {}

    result = {
        "question_id": str(row["id"]),
        "source_exam_code": row["source_exam_code"],
        "source_module_code": row["source_module_code"],
        "source_question_number": row["source_question_number"],
        "question_text": row["current_question_text"],
        "passage_text": row.get("current_passage_text"),
        "paired_passage_text": row.get("current_paired_passage_text"),
        "correct_option_label": row["current_correct_option_label"],
        "classification": {
            "domain": domain,
            "skill_family_key": sfk,
            "grammar_focus_key": gfk or None,
            "reading_focus_key": rfk or None,
            "difficulty_overall": difficulty or None,
            "difficulty_reading": ann.get("difficulty_reading"),
            "difficulty_grammar": ann.get("difficulty_grammar"),
            "difficulty_inference": ann.get("difficulty_inference"),
            "difficulty_vocab": ann.get("difficulty_vocab"),
            "distractor_strength": ann.get("distractor_strength"),
            "stem_type_key": stem_type,
            "stimulus_mode_key": stimulus,
            "syntactic_trap_key": ann.get("syntactic_trap_key"),
            "topic_broad": ann.get("topic_broad"),
            "topic_fine": ann.get("topic_fine"),
            "answer_mechanism_key": ann.get("answer_mechanism_key"),
            "solver_pattern_key": ann.get("solver_pattern_key"),
            "evidence_scope_key": ann.get("evidence_scope_key"),
            "classification_rationale": ann.get("classification_rationale"),
        },
        "generation_profile": {
            "target_grammar_focus_key": gen_profile.get("target_grammar_focus_key") or gfk or None,
            "target_grammar_role_key": gen_profile.get("target_grammar_role_key"),
            "target_syntactic_trap_key": gen_profile.get("target_syntactic_trap_key"),
            "syntactic_trap_intensity": gen_profile.get("syntactic_trap_intensity"),
            "target_frequency_band": gen_profile.get("target_frequency_band"),
            "passage_template": gen_profile.get("passage_template"),
            "model_version": gen_profile.get("model_version"),
        },
        "explanation": {
            "short": ann.get("explanation_short"),
            "full": ann.get("explanation_full"),
        },
        "options": options_out,
        "quality_flags": flags,
        "calibration_eligible": len([f for f in flags if "missing_domain" not in f or not flags]) == 0,
        "is_grammar": is_grammar,
        "is_reading": is_reading,
        "annotation_confidence": (ann.get("review") or {}).get("annotation_confidence") or ann.get("annotation_confidence"),
    }

    result["calibration_eligible"] = (
        bool(domain)
        and bool(difficulty)
        and (is_grammar or is_reading)
        and (not is_grammar or bool(gfk))
        and gfk_valid
    )

    return result


def select_calibration_candidates(all_classified: list[dict]) -> dict:
    """Select 20 grammar + 20 reading questions for the calibration batch."""

    grammar_eligible = [q for q in all_classified
                        if q["is_grammar"] and q["calibration_eligible"]
                        and q["classification"]["grammar_focus_key"]]

    reading_eligible = [q for q in all_classified
                        if q["is_reading"] and q["calibration_eligible"]]

    # ── Grammar: one per grammar_focus_key in priority order ──────────────────
    grammar_selected = []
    grammar_by_key: dict[str, list] = defaultdict(list)
    for q in grammar_eligible:
        grammar_by_key[q["classification"]["grammar_focus_key"]].append(q)

    used_ids: set[str] = set()

    def best_from(candidates: list) -> dict:
        return sorted(
            candidates,
            key=lambda q: (
                0 if q["classification"]["difficulty_overall"] == "medium" else 1,
                -(q["annotation_confidence"] or 0),
            )
        )[0]

    for key in PRIORITY_GRAMMAR_KEYS:
        if key in grammar_by_key and len(grammar_selected) < 20:
            candidate = best_from(grammar_by_key[key])
            if candidate["question_id"] not in used_ids:
                grammar_selected.append(candidate)
                used_ids.add(candidate["question_id"])

    # Fill any remaining slots from keys not in priority list
    for key, questions in grammar_by_key.items():
        if len(grammar_selected) >= 20:
            break
        for q in questions:
            if q["question_id"] not in used_ids:
                grammar_selected.append(q)
                used_ids.add(q["question_id"])
                break

    # ── Reading: spread across skill families, target 3-4 per family ──────────
    # Normalize skill_family_key to canonical names for grouping
    SFK_ALIASES = {
        # words in context
        "words_in_context": "words_in_context",
        "Words in Context": "words_in_context",
        # text structure
        "text_structure_and_purpose": "text_structure_and_purpose",
        "Text Structure and Purpose": "text_structure_and_purpose",
        # cross-text
        "cross_text_connections": "cross_text_connections",
        "Cross-Text Connections": "cross_text_connections",
        # central ideas
        "central_ideas_and_details": "central_ideas_and_details",
        "Central Ideas and Details": "central_ideas_and_details",
        # command of evidence
        "command_of_evidence": "command_of_evidence",
        "Command of Evidence": "command_of_evidence",
        # inferences
        "inferences": "inferences",
        "Inferences": "inferences",
        # rhetorical synthesis
        "rhetorical_synthesis": "rhetorical_synthesis",
        "Rhetorical Synthesis": "rhetorical_synthesis",
        "expression_of_ideas": "rhetorical_synthesis",
        "Expression of Ideas": "rhetorical_synthesis",
        "synthesis_of_information": "rhetorical_synthesis",
    }

    reading_by_canonical: dict[str, list] = defaultdict(list)
    for q in reading_eligible:
        sfk = q["classification"]["skill_family_key"] or ""
        canonical = SFK_ALIASES.get(sfk, sfk)
        reading_by_canonical[canonical].append(q)

    # Target allocation (sum must be <= 20)
    READING_TARGETS = {
        "words_in_context": 5,
        "central_ideas_and_details": 4,
        "text_structure_and_purpose": 4,
        "inferences": 3,
        "rhetorical_synthesis": 2,
        "command_of_evidence": 1,
        "cross_text_connections": 1,
    }

    reading_selected: list = []
    for canonical_key, target in READING_TARGETS.items():
        candidates = reading_by_canonical.get(canonical_key, [])
        # Sort: prefer varied reading_focus_key, then confidence
        seen_rfk: set[str] = set()
        for c in sorted(candidates, key=lambda q: -(q["annotation_confidence"] or 0)):
            if len(reading_selected) >= 20 or (len([r for r in reading_selected
                    if SFK_ALIASES.get(r["classification"]["skill_family_key"], "") == canonical_key]) >= target):
                break
            rfk = c["classification"].get("reading_focus_key") or ""
            if c["question_id"] not in used_ids and rfk not in seen_rfk:
                reading_selected.append(c)
                used_ids.add(c["question_id"])
                seen_rfk.add(rfk)

        # If we still have quota left and exhausted unique rfks, allow repeats
        for c in sorted(candidates, key=lambda q: -(q["annotation_confidence"] or 0)):
            current_in_family = len([r for r in reading_selected
                if SFK_ALIASES.get(r["classification"]["skill_family_key"], "") == canonical_key])
            if len(reading_selected) >= 20 or current_in_family >= target:
                break
            if c["question_id"] not in used_ids:
                reading_selected.append(c)
                used_ids.add(c["question_id"])

    # Store the canonical sfk on each selected reading question for reporting
    for q in reading_selected:
        sfk = q["classification"]["skill_family_key"] or ""
        q["classification"]["skill_family_key_canonical"] = SFK_ALIASES.get(sfk, sfk)

    return {
        "grammar": grammar_selected[:20],
        "reading": reading_selected[:20],
        "negative_controls_needed": 10,
        "negative_controls_note": (
            "Must be generated separately: 10 deliberately weak questions "
            "(low-quality prompt, no source examples, mixed grammar_focus_key + reading). "
            "See TASKS_GENERATION.md calibration plan."
        ),
    }


def main():
    out_dir = "/home/jb/DSAT_REDUX_MD/analysis/calibration"
    os.makedirs(out_dir, exist_ok=True)

    conn = psycopg2.connect(DB_DSN)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    print("Querying official questions...")
    cur.execute("""
        SELECT
            q.id,
            q.source_exam_code,
            q.source_module_code,
            q.source_question_number,
            q.stimulus_mode_key,
            q.stem_type_key,
            q.current_question_text,
            q.current_passage_text,
            q.current_paired_passage_text,
            q.current_correct_option_label,
            q.practice_status,
            q.is_canonical_source,
            qa.annotation_jsonb,
            qa.generation_profile_jsonb
        FROM questions q
        LEFT JOIN question_annotations qa ON qa.id = q.latest_annotation_id
        WHERE q.content_origin = 'official'
        ORDER BY q.source_exam_code, q.source_module_code, q.source_question_number
    """)

    rows = cur.fetchall()
    print(f"Found {len(rows)} official questions")

    all_classified = []
    flag_summary = defaultdict(int)

    for row in rows:
        classified = classify_question(dict(row))
        all_classified.append(classified)
        for flag in classified["quality_flags"]:
            flag_summary[flag.split(":")[0]] += 1

    # Summary stats
    total = len(all_classified)
    eligible = sum(1 for q in all_classified if q["calibration_eligible"])
    grammar_eligible = sum(1 for q in all_classified if q["is_grammar"] and q["calibration_eligible"])
    reading_eligible = sum(1 for q in all_classified if q["is_reading"] and q["calibration_eligible"])

    print(f"\nTotal: {total}")
    print(f"Calibration eligible: {eligible}")
    print(f"  Grammar eligible: {grammar_eligible}")
    print(f"  Reading eligible: {reading_eligible}")
    print(f"\nFlag summary:")
    for flag, count in sorted(flag_summary.items(), key=lambda x: -x[1]):
        print(f"  {flag}: {count}")

    # Select calibration candidates
    print("\nSelecting calibration set...")
    calibration = select_calibration_candidates(all_classified)

    # Write all classifications
    all_out = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "rules_version": "rules_agent_v7.0 + rules_agent_dsat_reading_v2",
        "total_official_questions": total,
        "calibration_eligible": eligible,
        "flag_summary": dict(flag_summary),
        "questions": all_classified,
    }

    all_path = os.path.join(out_dir, "official_classifications.json")
    with open(all_path, "w") as f:
        json.dump(all_out, f, indent=2, default=str)
    print(f"\nWrote {all_path}")

    # Write calibration set
    cal_out = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "rules_version": "rules_agent_v7.0 + rules_agent_dsat_reading_v2",
        "calibration_plan": {
            "grammar_count": len(calibration["grammar"]),
            "reading_count": len(calibration["reading"]),
            "negative_controls_needed": calibration["negative_controls_needed"],
            "negative_controls_note": calibration["negative_controls_note"],
        },
        "grammar_questions": calibration["grammar"],
        "reading_questions": calibration["reading"],
    }

    cal_path = os.path.join(out_dir, "calibration_set.json")
    with open(cal_path, "w") as f:
        json.dump(cal_out, f, indent=2, default=str)
    print(f"Wrote {cal_path}")

    # Write markdown report
    grammar_key_dist = defaultdict(int)
    for q in calibration["grammar"]:
        grammar_key_dist[q["classification"]["grammar_focus_key"]] += 1

    reading_sfk_dist = defaultdict(int)
    for q in calibration["reading"]:
        reading_sfk_dist[q["classification"].get("skill_family_key_canonical") or q["classification"]["skill_family_key"]] += 1

    report_lines = [
        "# Calibration Set Report",
        f"\nGenerated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        f"Rules: `rules_agent_v7.0` + `rules_agent_dsat_reading_v2`",
        "",
        "## Overall DB Stats",
        f"- Total official questions: **{total}**",
        f"- Calibration eligible: **{eligible}**",
        f"  - Grammar eligible: {grammar_eligible}",
        f"  - Reading eligible: {reading_eligible}",
        "",
        "## Quality Flags Found",
        "| Flag | Count |",
        "|---|---|",
    ]
    for flag, count in sorted(flag_summary.items(), key=lambda x: -x[1]):
        report_lines.append(f"| `{flag}` | {count} |")

    report_lines += [
        "",
        "## Selected Calibration Set (40 questions)",
        "",
        "### Grammar Questions (20)",
        "| # | Exam | Q# | grammar_focus_key | skill_family | Difficulty |",
        "|---|---|---|---|---|---|",
    ]
    for i, q in enumerate(calibration["grammar"], 1):
        c = q["classification"]
        report_lines.append(
            f"| {i} | PT{q['source_exam_code']} {q['source_module_code']} "
            f"| Q{q['source_question_number']} "
            f"| `{c['grammar_focus_key']}` "
            f"| {c['skill_family_key']} "
            f"| {c['difficulty_overall']} |"
        )

    report_lines += [
        "",
        "### Grammar Focus Key Distribution",
        "| grammar_focus_key | count |",
        "|---|---|",
    ]
    for key, count in sorted(grammar_key_dist.items(), key=lambda x: -x[1]):
        report_lines.append(f"| `{key}` | {count} |")

    report_lines += [
        "",
        "### Reading Questions (20)",
        "| # | Exam | Q# | skill_family_key | reading_focus_key | Difficulty |",
        "|---|---|---|---|---|---|",
    ]
    for i, q in enumerate(calibration["reading"], 1):
        c = q["classification"]
        report_lines.append(
            f"| {i} | PT{q['source_exam_code']} {q['source_module_code']} "
            f"| Q{q['source_question_number']} "
            f"| {c['skill_family_key']} "
            f"| {c['reading_focus_key']} "
            f"| {c['difficulty_overall']} |"
        )

    report_lines += [
        "",
        "### Reading Skill Family Distribution",
        "| skill_family_key | count |",
        "|---|---|",
    ]
    for key, count in sorted(reading_sfk_dist.items(), key=lambda x: -x[1]):
        report_lines.append(f"| {key} | {count} |")

    report_lines += [
        "",
        "## Negative Controls (10 — NOT YET GENERATED)",
        "",
        calibration["negative_controls_note"],
        "",
        "These must be generated with deliberately weak prompts (no source examples,",
        "mixed grammar_focus_key + reading targets) to serve as true negative controls.",
        "Generate them via `POST /generate/batches` with a dedicated batch.",
        "",
        "## Next Steps",
        "1. Run the review swarm against these 40 official questions",
        "2. Admin labels each `would_approve` / `would_reject` / `borderline`",
        "3. Generate 10 weak negative controls and add to the swarm run",
        "4. Pick consensus thresholds at the inflection where admin rejection rate flips",
        "5. Update `CONSENSUS_THRESHOLDS` in `backend/app/config.py`",
    ]

    report_path = os.path.join(out_dir, "calibration_report.md")
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))
    print(f"Wrote {report_path}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
