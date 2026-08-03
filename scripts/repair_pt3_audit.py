"""One-time repair of 2024 PT3 verbal questions per 2024_PT3_audit.md review.

Three changes, all in Module 2B:
  * Q13  answer C -> B  (graph: lowest spray 15.5% > highest spin 13.6%)
  * Q19  answer A -> C  ('however' is parenthetical, needs commas both sides)
  * Q4   INSERT         (absent from the DB; answer A, 'repudiates')

Also restores Q19's choice C option text, which was stored as 'nickname, however;'
(a duplicate of B) instead of the source's 'nickname, however,'.

Q4's UUID is derived with the same deterministic UUID5 scheme the ingestion
pipeline uses (backend/app/routers/ingest.py::_official_question_uuid), so a
future re-ingestion of this module is idempotent rather than creating a
duplicate row.

Existing rows are edited in place rather than by minting new version rows: they
have zero user_progress attempts, and the stored content encodes a wrong reading
of each question rather than a legitimate earlier state. Same approach as the
PT1 Q13 (bug-819) and PT2 (bug-821) repairs.

Run:  python3 scripts/repair_pt3_audit.py [--commit]
Without --commit the transaction is rolled back and only the statement log prints.
"""

import argparse
import json
import subprocess
import sys
import uuid

DB = ["docker", "exec", "-i", "dsat-db", "psql", "-U", "dsat", "-d", "dsat_dev"]

TEST = "Test03_ENG_Sec01_Mod02B"
NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # RFC 4122 URL namespace

# Annotation provenance copied from the sibling rows ingested in the same run.
PROVIDER = "ollama"
MODEL = "deepseek-v4-pro:cloud"
PROMPT_VERSION = "v8.0"
RULES_VERSION = "rules_agent_dsat_grammar_ingestion_generation_v8"


def official_question_uuid(n, year=2024, exam="03", subject="verbal", section="01", module="02B"):
    """Mirror of ingest.py::_official_question_uuid for this module."""
    parts = [f"Y{year}", TEST.upper(), exam.upper(), subject.lower(), section, module, str(n)]
    return str(uuid.uuid5(NS, ":".join(parts)))


# --- Q13 -------------------------------------------------------------------
# Graph values read at 300 dpi: spray 15.5 (lowest) / 17.3 (highest);
# spin 11.7 (lowest) / 13.6 (highest).
Q13 = {
    "qnum": 13,
    "new_answer": "B",
    "focus": "data_supports_claim",
    "explanation": (
        "Choice B is correct because it states a relationship the graph actually "
        "shows and that bears on the conclusion. Taylor and colleagues concluded "
        "that spray coating holds promise for improving the power conversion "
        "efficiency of ETLs. In the graph the lowest performing spray-coated ETL "
        "reaches about 15.5 percent, which is higher than the highest performing "
        "spin-coated ETL at about 13.6 percent. Even the worst spray-coated layer "
        "outperforms the best spin-coated layer, which is direct support for "
        "spray coating being the more promising method."
    ),
    "options": {
        "A": {
            "dtk": "detail_trap",
            "why_plausible": (
                "Both lowest-performing bars do sit above 10 percent, so the "
                "statement reads as an accurate description of the graph."
            ),
            "why_wrong": (
                "It is true but does not support the conclusion. Saying both "
                "methods clear 10 percent describes what they have in common and "
                "draws no comparison between them, so it gives no reason to "
                "prefer spray coating."
            ),
        },
        "B": {
            "dtk": "correct",
            "why_plausible": (
                "The lowest spray-coated value of about 15.5 percent exceeds the "
                "highest spin-coated value of about 13.6 percent, so spray "
                "coating outperforms spin coating across the whole tested range."
            ),
            "why_wrong": None,
        },
        "C": {
            "dtk": "wrong_value_read",
            "why_plausible": (
                "It compares the highest performing layer of each method, which "
                "is the right kind of comparison, and cites specific figures."
            ),
            "why_wrong": (
                "Both figures misread the graph. The highest performing "
                "spray-coated ETL is about 17.3 percent, not 13 percent, and the "
                "highest performing spin-coated ETL is about 13.6 percent, not 11 "
                "percent. The comparison it describes is not the one the graph "
                "shows."
            ),
        },
        "D": {
            "dtk": "single_measure_focus",
            "why_plausible": (
                "There is a visible gap between the lowest and highest "
                "spray-coated bars, so the statement looks defensible."
            ),
            "why_wrong": (
                "It compares spray coating only to itself and never mentions spin "
                "coating, so it cannot support a conclusion about spray coating "
                "being the better method. The roughly 1.8-point spread is also "
                "small next to the gap between the two methods."
            ),
        },
    },
}

# --- Q19 -------------------------------------------------------------------
# Source choices: A 'nickname, however'  B 'nickname, however;'
#                 C 'nickname, however,' D 'nickname; however,'
# The DB stored C as 'nickname, however;', duplicating B.
Q19 = {
    "qnum": 19,
    "new_answer": "C",
    "focus": "punctuation_comma",
    "option_texts": {
        "A": "nickname, however",
        "B": "nickname, however;",
        "C": "nickname, however,",
        "D": "nickname; however,",
    },
    "explanation": (
        "Choice C is correct because 'however' here is a parenthetical inserted "
        "into a single clause and must be set off by commas on both sides. The "
        "sentence is 'Scott-Heron himself resisted the godfather nickname, "
        "however, feeling that it didn't encapsulate his devotion to the broader "
        "African American blues music tradition.' What follows the blank is the "
        "participial phrase 'feeling that ...', not an independent clause, so no "
        "sentence-splitting punctuation is available here: the comma after "
        "'however' closes the parenthetical and lets the participial phrase "
        "attach to the main clause."
    ),
    "options": {
        "A": {
            "dtk": "missing_necessary_punctuation",
            "why_plausible": (
                "It opens the parenthetical correctly with a comma before "
                "'however', so the first half of the punctuation is right."
            ),
            "why_wrong": (
                "It never closes the parenthetical. With no comma after "
                "'however', that word runs into the participial phrase 'feeling "
                "that ...', leaving the interrupter unbounded on one side."
            ),
        },
        "B": {
            "dtk": "semicolon_use",
            "why_plausible": (
                "Semicolons often appear next to 'however', so the pairing looks "
                "familiar."
            ),
            "why_wrong": (
                "A semicolon must join two independent clauses, but 'feeling that "
                "it didn't encapsulate his devotion ...' is a participial phrase "
                "with no subject or finite verb and cannot stand alone."
            ),
        },
        "C": {
            "dtk": "correct",
            "why_plausible": (
                "Commas on both sides bound 'however' as a parenthetical, and the "
                "closing comma lets the participial phrase 'feeling that ...' "
                "attach to the main clause."
            ),
            "why_wrong": None,
        },
        "D": {
            "dtk": "semicolon_use",
            "why_plausible": (
                "Semicolon-then-'however'-then-comma is the standard pattern when "
                "'however' opens a new independent clause, so it looks correct in "
                "isolation."
            ),
            "why_wrong": (
                "That pattern requires an independent clause on each side. Here "
                "the semicolon would cut 'however, feeling that ...' off from the "
                "main clause, leaving a fragment, and it also wrongly attaches "
                "'however' to what follows rather than to the resistance just "
                "described."
            ),
        },
    },
}

# --- Q4 (insert) -----------------------------------------------------------
Q4 = {
    "qnum": 4,
    "new_answer": "A",
    "focus": "contextual_meaning",
    "question_text": (
        "Which choice completes the text with the most logical and precise word or phrase?"
    ),
    "passage_text": (
        "Seminole/Muscogee director Sterlin Harjo ______ television's tendency to "
        "situate Native characters in the distant past: this rejection is evident "
        "in his series Reservation Dogs, which revolves around teenagers who "
        "dress in contemporary styles and whose dialogue is laced with current "
        "slang."
    ),
    "explanation": (
        "Choice A is correct because 'repudiates' means rejects or refuses to "
        "accept, which is exactly what the sentence goes on to describe. The "
        "colon introduces an explanation that names the action directly: 'this "
        "rejection is evident in his series Reservation Dogs.' Because the text "
        "labels Harjo's stance a rejection, the blank must carry that sense, and "
        "the examples that follow — teenagers in contemporary styles using "
        "current slang — show him working against television's tendency to "
        "confine Native characters to the distant past."
    ),
    "options": {
        "A": {
            "text": "repudiates",
            "dtk": "correct",
            "why_plausible": (
                "'Repudiates' means rejects, matching the text's own description "
                "of Harjo's stance as 'this rejection'."
            ),
            "why_wrong": None,
        },
        "B": {
            "text": "proclaims",
            "dtk": "semantic_imprecision",
            "why_plausible": (
                "'Proclaims' suggests taking a strong public stance, and Harjo "
                "does make his position visible through his work."
            ),
            "why_wrong": (
                "It means announces or declares, so it would have Harjo endorsing "
                "television's tendency rather than rejecting it. That reverses the "
                "relationship the colon spells out."
            ),
        },
        "C": {
            "text": "foretells",
            "dtk": "semantic_imprecision",
            "why_plausible": (
                "The passage contrasts the distant past with the present, so a "
                "word about time can seem to fit."
            ),
            "why_wrong": (
                "'Foretells' means predicts a future event. Harjo is not "
                "predicting television's tendency; he is opposing an existing one."
            ),
        },
        "D": {
            "text": "recants",
            "dtk": "semantic_imprecision",
            "why_plausible": (
                "'Recants' also expresses rejection, so it is close to the "
                "required meaning and is the strongest distractor."
            ),
            "why_wrong": (
                "To recant is to withdraw a belief one previously held oneself. "
                "The tendency being rejected belongs to television generally, not "
                "to Harjo, so he cannot recant it."
            ),
        },
    },
    "annotation": {
        "tone": "neutral",
        "domain": "Craft and Structure",
        "register": "academic informational",
        "graph_data": None,
        "table_data": None,
        "topic_fine": "film and television",
        "topic_broad": "arts and humanities",
        "notes_bullets": [],
        "reading_scope": "passage-level",
        "stem_type_key": "choose_words_in_context",
        "difficulty_vocab": "hard",
        "grammar_role_key": None,
        "reasoning_demand": "contextual_substitution",
        "skill_family_key": "words_in_context",
        "grammar_focus_key": None,
        "reading_focus_key": "contextual_meaning",
        "stimulus_mode_key": "passage_excerpt",
        "difficulty_grammar": None,
        "difficulty_overall": "hard",
        "difficulty_reading": "medium",
        "evidence_scope_key": "passage",
        "evidence_span_text": (
            "this rejection is evident in his series Reservation Dogs, which "
            "revolves around teenagers who dress in contemporary styles and whose "
            "dialogue is laced with current slang"
        ),
        "reasoning_trap_key": "semantic_imprecision",
        "solver_pattern_key": "substitute_and_test",
        "distractor_strength": "high",
        "paired_passage_text": None,
        "question_family_key": "craft_and_structure",
        "answer_mechanism_key": "contextual_substitution",
        "difficulty_inference": "low",
        "evidence_location_key": "main_clause",
        "classification_rationale": (
            "The colon introduces an appositive explanation naming Harjo's stance "
            "as 'this rejection', so the blank must mean rejects. 'Recants' is the "
            "primary trap: it also denotes rejection but requires the belief to "
            "have been the subject's own, which does not hold here."
        ),
        "secondary_reading_focus_keys": [],
    },
}


def psql(sql, mode="-t"):
    r = subprocess.run(DB + [mode, "-A", "-c", sql], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"psql failed:\n{r.stderr}")
    return r.stdout.strip()


def q(v):
    if v is None:
        return "NULL"
    return "'" + str(v).replace("'", "''") + "'"


def jq(obj):
    return q(json.dumps(obj)) + "::jsonb"


def update_statements(rep):
    """Statements for an existing row (Q13, Q19)."""
    stmts = []
    qnum, ans = rep["qnum"], rep["new_answer"]
    where_v = (
        "(SELECT latest_version_id FROM questions WHERE source_test_name="
        f"{q(TEST)} AND source_question_number={qnum})"
    )

    if rep.get("option_texts"):
        for lab, txt in rep["option_texts"].items():
            stmts.append(
                f"UPDATE question_options SET option_text={q(txt)} "
                f"WHERE question_version_id={where_v} AND option_label='{lab}';"
            )

    for lab, o in rep["options"].items():
        ok = lab == ans
        stmts.append(
            "UPDATE question_options SET "
            f"is_correct={'true' if ok else 'false'}, "
            f"option_role={q('correct' if ok else 'distractor')}, "
            f"why_plausible={q(o['why_plausible'])}, why_wrong={q(o['why_wrong'])}, "
            f"grammar_fit={q('yes' if ok else 'no')}, precision_score={3 if ok else 1}, "
            f"distractor_type_key={q(o['dtk'])}, "
            f"option_error_focus_key={'NULL' if ok else q(rep['focus'])} "
            f"WHERE question_version_id={where_v} AND option_label='{lab}';"
        )

    sets = [f"correct_option_label={q(ans)}", f"explanation_text={q(rep['explanation'])}"]
    if rep.get("option_texts"):
        arr = [{"label": l, "text": rep["option_texts"][l]} for l in "ABCD"]
        sets.append(f"choices_jsonb={jq(arr)}")
    stmts.append(f"UPDATE question_versions SET {', '.join(sets)} WHERE id={where_v};")

    stmts.append(
        f"UPDATE questions SET current_correct_option_label={q(ans)}, "
        f"current_explanation_text={q(rep['explanation'])}, annotation_stale=false, "
        f"updated_at=now() WHERE source_test_name={q(TEST)} AND source_question_number={qnum};"
    )

    stmts.append(sync_annotation_sql(where_v, ans, rep["explanation"], qnum))
    return stmts


def sync_annotation_sql(where_v, ans, explanation, qnum):
    """Rebuild annotation options[] from the repaired option rows and resync scalars.

    Targets the annotation by questions.latest_annotation_id rather than by
    question_version_id: 408 of 1489 rows database-wide have a latest annotation
    whose question_version_id points at a superseded version (PT3 M2B Q13 is one),
    so keying on the version id would silently update nothing.
    """
    return (
        "UPDATE question_annotations a SET annotation_jsonb = "
        "jsonb_set(jsonb_set(jsonb_set(a.annotation_jsonb, '{options}', ("
        "  SELECT jsonb_agg(jsonb_build_object("
        "    'option_label', o.option_label, 'option_text', o.option_text,"
        "    'is_correct', o.is_correct, 'option_role', o.option_role,"
        "    'why_plausible', o.why_plausible, 'why_wrong', o.why_wrong,"
        "    'grammar_fit', o.grammar_fit, 'tone_match', o.tone_match,"
        "    'precision_score', o.precision_score,"
        "    'distractor_type_key', o.distractor_type_key,"
        "    'semantic_relation_key', o.semantic_relation_key,"
        "    'option_error_focus_key', o.option_error_focus_key,"
        "    'plausibility_source_key', o.plausibility_source_key"
        "  ) ORDER BY o.option_label)"
        f"  FROM question_options o WHERE o.question_version_id={where_v}"
        f")), '{{correct_option_label}}', {q(json.dumps(ans))}::jsonb), "
        f"'{{explanation_full}}', {q(json.dumps(explanation))}::jsonb), "
        f"explanation_jsonb = jsonb_build_object('explanation_full', {q(explanation)}) "
        "WHERE a.id=(SELECT latest_annotation_id FROM questions WHERE source_test_name="
        f"{q(TEST)} AND source_question_number={qnum});"
    )


def insert_statements(rep):
    """Statements creating the missing Q4 row, version, options and annotation."""
    qid = official_question_uuid(rep["qnum"])
    vid = str(uuid.uuid4())
    aid = str(uuid.uuid4())
    ans = rep["new_answer"]
    choices = [{"label": l, "text": rep["options"][l]["text"]} for l in "ABCD"]

    ann = dict(rep["annotation"])
    ann.update({
        "prompt_text": rep["question_text"],
        "passage_text": rep["passage_text"],
        "source_exam": TEST,
        "source_module": "02B",
        "source_section": "01",
        "source_question_number": rep["qnum"],
        "correct_option_label": ans,
        "explanation_full": rep["explanation"],
        "explanation_short": (
            "The colon explains that Harjo's stance is a rejection of television's "
            "tendency, so the blank needs a word meaning rejects: 'repudiates'."
        ),
        "options": [
            {
                "option_label": l,
                "option_text": rep["options"][l]["text"],
                "is_correct": l == ans,
                "option_role": "correct" if l == ans else "distractor",
                "why_plausible": rep["options"][l]["why_plausible"],
                "why_wrong": rep["options"][l]["why_wrong"],
                "grammar_fit": "yes",
                "tone_match": "yes",
                "precision_score": 3 if l == ans else 1,
                "distractor_type_key": rep["options"][l]["dtk"],
                "semantic_relation_key": None,
                "option_error_focus_key": None if l == ans else rep["focus"],
                "plausibility_source_key": None,
            }
            for l in "ABCD"
        ],
    })

    stmts = [
        # questions row; latest_* set after the version and annotation exist
        "INSERT INTO questions (id, content_origin, source_exam_code, source_subject_code, "
        "source_section_code, source_module_code, source_question_number, source_release_year, "
        "source_test_name, stimulus_mode_key, stem_type_key, current_question_text, "
        "current_passage_text, current_correct_option_label, current_explanation_text, "
        "practice_status, official_overlap_status, is_admin_edited, metadata_managed_by_llm, "
        "annotation_stale, is_canonical_source) VALUES ("
        f"'{qid}', 'official', '03', 'verbal', '01', '02B', {rep['qnum']}, 2024, {q(TEST)}, "
        f"{q(rep['annotation']['stimulus_mode_key'])}, {q(rep['annotation']['stem_type_key'])}, "
        f"{q(rep['question_text'])}, {q(rep['passage_text'])}, {q(ans)}, {q(rep['explanation'])}, "
        "'active', 'none', false, true, false, false);",

        f"INSERT INTO question_versions (id, question_id, version_number, change_source, "
        f"question_text, passage_text, choices_jsonb, correct_option_label, explanation_text, "
        f"change_notes) VALUES ('{vid}', '{qid}', 1, 'ingest', {q(rep['question_text'])}, "
        f"{q(rep['passage_text'])}, {jq(choices)}, {q(ans)}, {q(rep['explanation'])}, "
        f"{q('Backfilled from source PDF; absent from original ingestion (2024_PT3_audit.md).')});",
    ]

    for l in "ABCD":
        o = rep["options"][l]
        ok = l == ans
        stmts.append(
            "INSERT INTO question_options (id, question_id, question_version_id, option_label, "
            "option_text, is_correct, option_role, distractor_type_key, option_error_focus_key, "
            "why_plausible, why_wrong, grammar_fit, tone_match, precision_score) VALUES ("
            f"'{uuid.uuid4()}', '{qid}', '{vid}', '{l}', {q(o['text'])}, "
            f"{'true' if ok else 'false'}, {q('correct' if ok else 'distractor')}, "
            f"{q(o['dtk'])}, {'NULL' if ok else q(rep['focus'])}, "
            f"{q(o['why_plausible'])}, {q(o['why_wrong'])}, 'yes', 'yes', {3 if ok else 1});"
        )

    stmts.append(
        "INSERT INTO question_annotations (id, question_id, question_version_id, provider_name, "
        "model_name, prompt_version, rules_version, annotation_jsonb, explanation_jsonb, "
        f"confidence_jsonb) VALUES ('{aid}', '{qid}', '{vid}', {q(PROVIDER)}, {q(MODEL)}, "
        f"{q(PROMPT_VERSION)}, {q(RULES_VERSION)}, {jq(ann)}, "
        f"{jq({'explanation_full': rep['explanation']})}, "
        f"{jq({'needs_human_review': True, 'annotation_confidence': 0.0})});"
    )

    stmts.append(
        f"UPDATE questions SET latest_version_id='{vid}', latest_annotation_id='{aid}' "
        f"WHERE id='{qid}';"
    )
    return stmts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    args = ap.parse_args()

    existing = psql(
        f"SELECT count(*) FROM questions WHERE source_test_name={q(TEST)} AND source_question_number=4;"
    )
    stmts = []
    if existing == "0":
        stmts += insert_statements(Q4)
    else:
        print("NOTE: Q4 already present; skipping insert.")
    stmts += update_statements(Q13)
    stmts += update_statements(Q19)

    sql = "BEGIN;\n" + "\n".join(stmts) + ("\nCOMMIT;" if args.commit else "\nROLLBACK;")
    r = subprocess.run(DB + ["-v", "ON_ERROR_STOP=1"], input=sql, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"transaction failed (rolled back):\n{r.stderr}")
    print(r.stdout.strip()[-300:])
    print(f"\n{len(stmts)} statements {'COMMITTED' if args.commit else 'rolled back (dry run)'}")


if __name__ == "__main__":
    main()
