"""One-time repair of 2024 PT2 verbal questions per 2024_PT2_audit.md review.

Applies four answer-key corrections (M1 Q17 B->D, M1 Q19 A->C, M2A Q11 C->D,
M2B Q21 B->A), restores M1 Q19's corrupted option texts and M2B Q7's passage
from the source PDFs, and rewrites explanations plus per-option distractor
rationales on every touched question.

Edits the latest version row in place rather than minting a new version: these
rows have zero user_progress attempts, so no student answer data is invalidated,
and the existing rows encode a wrong reading of the questions rather than a
legitimate earlier state. Same approach as the PT1 Q13 repair (bug-819).

Run:  python3 scripts/repair_pt2_audit.py [--commit]
Without --commit the transaction is rolled back and only the diff is printed.
"""

import argparse
import json
import subprocess
import sys

DB = ["docker", "exec", "-i", "dsat-db", "psql", "-U", "dsat", "-d", "dsat_dev"]

# --- source-of-truth content, transcribed from the rendered PDF pages ---------

M2B_Q7_PASSAGE = (
    "For many years, the only existing fossil evidence of mixopterid "
    "eurypterids—an extinct family of large aquatic arthropods known as sea "
    "scorpions and related to modern arachnids and horseshoe crabs—came from "
    "four species living on the paleocontinent of Laurussia. In a discovery that "
    "expands our understanding of the geographical distribution of mixopterids, "
    "paleontologist Bo Wang and others have identified fossilized remains of a "
    "new mixopterid species, Terropterus xiushanensis, that lived over 400 "
    "million years ago on the paleocontinent of Gondwana."
)

# M1 Q19: every option was stored ending in a semicolon. Only A ends that way
# in the source; B, C and D end in a comma.
M1_Q19_OPTIONS = {
    "A": "Basic; in 2009, an online television network;",
    "B": "Basic; in 2009, an online television network,",
    "C": "Basic, in 2009; an online television network,",
    "D": "Basic, in 2009, an online television network,",
}

REPAIRS = [
    {
        "qid": "e71509cd-e182-5574-9d1c-4466e1070a2f",
        "label": "M1 Q17",
        "focus": 'punctuation_comma',
        "new_answer": "D",
        "explanation": (
            "Choice D is correct because no punctuation belongs between the "
            "complementizer 'that' and the clause it introduces. The sentence "
            "gives two reasons why gathering water-flow data is challenging, "
            "coordinated as objects of 'because of': the country's millions of "
            "miles of waterways, and the fact that the volume and speed of "
            "water can vary drastically. Reading straight through, 'because of "
            "the country's millions of miles of waterways and the fact that the "
            "volume and speed of water at any given location can vary "
            "drastically over time' is complete and correctly punctuated."
        ),
        "options": {
            "A": {
                "dtk": 'unnecessary_internal_punctuation',
                "why_plausible": (
                    "Leaves the coordination unpunctuated, which is correct, so "
                    "the choice looks right until the trailing comma is noticed."
                ),
                "why_wrong": (
                    "The comma after 'that' severs the complementizer from the "
                    "clause it introduces ('the volume and speed of water ... "
                    "can vary'). A noun clause cannot be separated from 'that' "
                    "by a comma."
                ),
            },
            "B": {
                "dtk": 'unnecessary_internal_punctuation',
                "why_plausible": (
                    "The comma before 'and' looks like the standard way to join "
                    "two long elements, which makes this the most tempting "
                    "distractor."
                ),
                "why_wrong": (
                    "Like A and C, it places a comma after 'that', cutting the "
                    "complementizer off from its clause. The comma before 'and' "
                    "is also unnecessary, since the two coordinated elements are "
                    "objects of 'because of', not independent clauses."
                ),
            },
            "C": {
                "dtk": 'unnecessary_internal_punctuation',
                "why_plausible": (
                    "Punctuating around 'and' can look like it is setting off "
                    "the second element for clarity."
                ),
                "why_wrong": (
                    "The comma after 'and' separates the conjunction from the "
                    "element it introduces, and no punctuation should interrupt "
                    "'and the fact that ...' at all."
                ),
            },
            "D": {
                "dtk": 'correct',
                "why_plausible": (
                    "No punctuation interrupts either the coordination or the "
                    "noun clause, so the sentence reads cleanly from 'because "
                    "of' through to the end."
                ),
                "why_wrong": None,
            },
        },
    },
    {
        "qid": "e090ec68-e75c-538a-a80c-4ebd601a1328",
        "label": "M1 Q19",
        "focus": 'semicolon_use',
        "new_answer": "C",
        "option_texts": M1_Q19_OPTIONS,
        "explanation": (
            "Choice C is correct because the sentence is a three-item series in "
            "which each product is paired with the year it appeared, and the "
            "items are separated by semicolons because they contain internal "
            "commas. The semicolon already present before 'and a Rosetta Stone "
            "language course' fixes the semicolon as the top-level separator. "
            "Choice C yields: 'the world's first Indigenous-language "
            "instructional app, Chickasaw Basic, in 2009; an online television "
            "network, Chickasaw TV, in 2010; and a Rosetta Stone language "
            "course in Chickasaw, in 2015.' The comma after 'Basic' attaches "
            "2009 to the app, the semicolon after '2009' closes the first item, "
            "and the final comma makes 'Chickasaw TV' an appositive renaming "
            "'an online television network'."
        ),
        "options": {
            "A": {
                "dtk": 'semicolon_use',
                "why_plausible": (
                    "Semicolons do separate items in a complex series, so the "
                    "semicolon after 'Basic' can look like the item break."
                ),
                "why_wrong": (
                    "Placing the item break after 'Basic' leaves the app "
                    "undated and attaches 2009 to the television network, which "
                    "the passage dates to 2010. The closing semicolon then also "
                    "cuts 'Chickasaw TV' off from the network it renames."
                ),
            },
            "B": {
                "dtk": 'semicolon_use',
                "why_plausible": (
                    "It ends with the comma needed before the appositive "
                    "'Chickasaw TV', so the second half of the choice is "
                    "correctly punctuated."
                ),
                "why_wrong": (
                    "The semicolon after 'Basic' breaks the series in the wrong "
                    "place. It separates 'Chickasaw Basic' from 'in 2009' and "
                    "hands that year to the television network, contradicting "
                    "the passage, which pairs Chickasaw TV with 2010."
                ),
            },
            "C": {
                "dtk": 'correct',
                "why_plausible": (
                    "Each product keeps its own date and the appositive stays "
                    "attached to the noun it renames, matching the semicolon "
                    "series already established before 'and a Rosetta Stone'."
                ),
                "why_wrong": None,
            },
            "D": {
                "dtk": 'missing_necessary_punctuation',
                "why_plausible": (
                    "Commas are the default series separator, and the choice "
                    "otherwise segments the sentence in the right places."
                ),
                "why_wrong": (
                    "Using only commas gives no way to tell the item boundaries "
                    "from the commas inside each item, so the series runs "
                    "together. A semicolon is required after '2009'."
                ),
            },
        },
    },
    {
        "qid": "00692e60-e927-5441-852d-a6706799d8cd",
        "label": "M2A Q11",
        "focus": 'data_supports_claim',
        "new_answer": "D",
        "explanation": (
            "Choice D is correct because the hypothesis is that plants respond "
            "to kanamycin by altering their uptake of metals such as iron and "
            "zinc, and the graph shows exactly that. In the control plants zinc "
            "is near 390 parts per million and iron near 625; in the plants "
            "exposed to kanamycin zinc falls to about 300 and iron to about "
            "225. Both metals are lower after exposure, which is a direct "
            "change in metal content between the two groups and therefore "
            "supports Ayalew and her colleagues' hypothesis."
        ),
        "options": {
            "A": {
                "dtk": 'data_context_mismatch',
                "why_plausible": (
                    "It contrasts the two groups, which is the right kind of "
                    "comparison for supporting the hypothesis."
                ),
                "why_wrong": (
                    "It misreads the graph in both groups. Iron is higher than "
                    "zinc in the control plants, not lower, and zinc is higher "
                    "than iron in the exposed plants, not lower. The stated "
                    "relationship is reversed."
                ),
            },
            "B": {
                "dtk": 'single_measure_focus',
                "why_plausible": (
                    "The claim is true of three of the four bars, so it looks "
                    "like an accurate reading of the graph."
                ),
                "why_wrong": (
                    "It reports no difference between the control and exposed "
                    "groups, so it cannot support a hypothesis about how "
                    "kanamycin exposure changes metal uptake. Iron in the "
                    "exposed plants is also near 225 ppm, just above the stated "
                    "threshold."
                ),
            },
            "C": {
                "dtk": 'direction_reversal',
                "why_plausible": (
                    "It cites zinc in both groups with specific figures, and "
                    "the numbers 300 and 400 do both appear on the graph."
                ),
                "why_wrong": (
                    "The values are swapped. Zinc is near 390 ppm in the "
                    "control plants and falls to about 300 ppm after kanamycin "
                    "exposure, so the graph shows a decrease, not the increase "
                    "described here."
                ),
            },
            "D": {
                "dtk": 'correct',
                "why_plausible": (
                    "It accurately reports both metals as lower in the exposed "
                    "plants, which is the change in metal uptake the hypothesis "
                    "predicts."
                ),
                "why_wrong": None,
            },
        },
    },
    {
        "qid": "907a4622-bbda-580a-9f2c-a76e3c1a53cc",
        "label": "M2B Q7",
        "focus": 'supporting_detail',
        "new_answer": "D",
        "passage": M2B_Q7_PASSAGE,
        "explanation": (
            "Choice D is correct because the text states that for many years "
            "the only known mixopterid fossils came from four species living on "
            "the paleocontinent of Laurussia, and that Wang and his team "
            "identified Terropterus xiushanensis on the paleocontinent of "
            "Gondwana. The discovery is framed as one that 'expands our "
            "understanding of the geographical distribution of mixopterids', so "
            "its significance is that it is the first evidence of mixopterids "
            "outside Laurussia."
        ),
        "options": {
            "A": {
                "dtk": 'detail_trap',
                "why_plausible": (
                    "The text does mention that the species lived over 400 "
                    "million years ago, so the figure is drawn from the passage."
                ),
                "why_wrong": (
                    "The age is offered as a detail about the new species, not "
                    "as what made the find significant. The text never says "
                    "this is the first evidence that mixopterids lived that long "
                    "ago; the stated significance is geographical."
                ),
            },
            "B": {
                "dtk": 'overreach',
                "why_plausible": (
                    "The passage does describe mixopterids as related to modern "
                    "arachnids and horseshoe crabs."
                ),
                "why_wrong": (
                    "That relationship is given as background about the family "
                    "as a whole. The text does not present the new fossil as "
                    "revising how closely mixopterids are related to those "
                    "animals."
                ),
            },
            "C": {
                "dtk": 'overreach',
                "why_plausible": (
                    "It names both paleocontinents the text discusses, so it "
                    "echoes the passage's key terms."
                ),
                "why_wrong": (
                    "The text describes a change in the known geographical "
                    "range of mixopterids, not a revised evolutionary timeline. "
                    "No timeline is proposed or corrected in the passage."
                ),
            },
            "D": {
                "dtk": 'correct',
                "why_plausible": (
                    "It matches the text's own framing of the discovery as "
                    "expanding the known geographical distribution of "
                    "mixopterids beyond Laurussia."
                ),
                "why_wrong": None,
            },
        },
    },
    {
        "qid": "075ac1b3-2ade-55bf-b1ea-ecb8b606a437",
        "label": "M2B Q19",
        "focus": 'conjunction_usage',
        "new_answer": "B",
        "explanation": (
            "Choice B is correct because it forms a supplementary absolute "
            "phrase describing the quilts: 'the portraits reveal themselves to "
            "be quilts, the stitching barely visible among the thousands of "
            "pieces of printed, microcut fabric.' An absolute phrase is a noun "
            "phrase plus a modifier that attaches to the main clause with a "
            "comma and adds detail about it, which is exactly the relationship "
            "between the quilts and their stitching here."
        ),
        "options": {
            "A": {
                "dtk": 'conjunction_usage',
                "why_plausible": (
                    "Adding 'and' looks like it is joining two things the "
                    "portraits are revealed to be."
                ),
                "why_wrong": (
                    "'The stitching barely visible' is not a second predicate "
                    "noun and has no finite verb, so it cannot be coordinated "
                    "with 'quilts'. The conjunction creates a false parallel."
                ),
            },
            "B": {
                "dtk": 'correct',
                "why_plausible": (
                    "The comma attaches the absolute phrase 'the stitching "
                    "barely visible ...' to the main clause, adding detail "
                    "about the quilts just described."
                ),
                "why_wrong": None,
            },
            "C": {
                "dtk": 'semicolon_use',
                "why_plausible": (
                    "A semicolon looks appropriate for adding a closely related "
                    "follow-on remark."
                ),
                "why_wrong": (
                    "A semicolon must join two independent clauses, but 'the "
                    "stitching barely visible among the thousands of pieces of "
                    "printed, microcut fabric' has no finite verb and cannot "
                    "stand alone."
                ),
            },
            "D": {
                "dtk": 'sentence_boundary',
                "why_plausible": (
                    "Ending the sentence after 'quilts' leaves a complete main "
                    "clause, so the first half is grammatical."
                ),
                "why_wrong": (
                    "The remaining words form a fragment. 'The stitching barely "
                    "visible ...' lacks a finite verb, so it cannot stand as its "
                    "own sentence."
                ),
            },
        },
    },
    {
        "qid": "16feddd1-882d-54be-8b23-8b4b1f3ff0a2",
        "label": "M2B Q21",
        "focus": 'conjunctive_adverb_usage',
        "new_answer": "A",
        "explanation": (
            "Choice A is correct because 'however' contrasts this sentence with "
            "the preceding one and belongs at the end of the first clause. The "
            "text says Okinaka sits on the review board, then that he doesn't "
            "make such decisions single-handedly; 'however' marks that contrast "
            "and is set off by a comma as a parenthetical closing that clause. "
            "The semicolon then joins the two independent clauses: 'Okinaka "
            "doesn't make such decisions single-handedly, however; all "
            "historical designations must be approved by a group of nine other "
            "experts.' The final clause explains why he cannot decide alone "
            "rather than contrasting with it, so 'however' cannot introduce it."
        ),
        "options": {
            "A": {
                "dtk": 'correct',
                "why_plausible": (
                    "'However' closes the clause it modifies, set off by a "
                    "comma, and the semicolon correctly joins the two "
                    "independent clauses."
                ),
                "why_wrong": None,
            },
            "B": {
                "dtk": 'conjunctive_adverb_placement',
                "why_plausible": (
                    "Semicolon-plus-'however'-plus-comma is the most familiar "
                    "conjunctive-adverb pattern, so it looks correct in "
                    "isolation."
                ),
                "why_wrong": (
                    "The punctuation is conventional, but it puts 'however' at "
                    "the head of the final clause, making that clause the "
                    "contrast. That clause instead explains why Okinaka cannot "
                    "decide alone, so the contrast is with the preceding "
                    "sentence and 'however' belongs at the end of the first "
                    "clause."
                ),
            },
            "C": {
                "dtk": 'comma_splice',
                "why_plausible": (
                    "It places 'however' at the end of the first clause, which "
                    "is the right position for the contrast."
                ),
                "why_wrong": (
                    "A comma alone cannot join two independent clauses. This "
                    "creates a comma splice between 'single-handedly, however' "
                    "and 'all historical designations must be approved'."
                ),
            },
            "D": {
                "dtk": 'sentence_boundary',
                "why_plausible": (
                    "Omitting punctuation avoids having to choose between the "
                    "comma and the semicolon."
                ),
                "why_wrong": (
                    "With no punctuation at all the two independent clauses run "
                    "together, and 'however' is left unmarked as a parenthetical."
                ),
            },
        },
    },
]


def psql(sql, mode="-t"):
    r = subprocess.run(DB + [mode, "-A", "-c", sql], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"psql failed:\n{r.stderr}")
    return r.stdout


def q(s):
    """Quote a Python value as a SQL literal."""
    if s is None:
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"


def build_statements():
    stmts = []
    for rep in REPAIRS:
        qid = rep["qid"]
        ans = rep["new_answer"]
        texts = rep.get("option_texts")

        # 1. option_text repairs (M1 Q19 only)
        if texts:
            for lab, txt in texts.items():
                stmts.append(
                    f"UPDATE question_options SET option_text={q(txt)} "
                    f"WHERE question_version_id=(SELECT latest_version_id FROM questions WHERE id='{qid}') "
                    f"AND option_label='{lab}';"
                )

        # 2. per-option correctness, role and rationales
        for lab, o in rep["options"].items():
            correct = lab == ans
            stmts.append(
                "UPDATE question_options SET "
                f"is_correct={'true' if correct else 'false'}, "
                f"option_role={q('correct' if correct else 'distractor')}, "
                f"why_plausible={q(o['why_plausible'])}, "
                f"why_wrong={q(o['why_wrong'])}, "
                f"grammar_fit={q('yes' if correct else 'no')}, "
                f"precision_score={3 if correct else 1}, "
                f"distractor_type_key={q('correct') if correct else q(o['dtk'])}, "
                f"option_error_focus_key={'NULL' if correct else q(rep['focus'])} "
                f"WHERE question_version_id=(SELECT latest_version_id FROM questions WHERE id='{qid}') "
                f"AND option_label='{lab}';"
            )

        # 3. version row: answer label, explanation, choices_jsonb, passage
        sets = [
            f"correct_option_label={q(ans)}",
            f"explanation_text={q(rep['explanation'])}",
        ]
        if texts:
            arr = json.dumps([{"label": l, "text": texts[l]} for l in "ABCD"])
            sets.append(f"choices_jsonb={q(arr)}::jsonb")
        if rep.get("passage"):
            sets.append(f"passage_text={q(rep['passage'])}")
        stmts.append(
            f"UPDATE question_versions SET {', '.join(sets)} "
            f"WHERE id=(SELECT latest_version_id FROM questions WHERE id='{qid}');"
        )

        # 4. denormalized columns on questions
        qsets = [
            f"current_correct_option_label={q(ans)}",
            f"current_explanation_text={q(rep['explanation'])}",
            "annotation_stale=false",
            "updated_at=now()",
        ]
        if rep.get("passage"):
            qsets.append(f"current_passage_text={q(rep['passage'])}")
        stmts.append(f"UPDATE questions SET {', '.join(qsets)} WHERE id='{qid}';")

        # 5. annotation_jsonb options[] rebuilt from the repaired option rows
        stmts.append(
            "UPDATE question_annotations a SET annotation_jsonb = "
            "jsonb_set(a.annotation_jsonb, '{options}', ("
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
            "  FROM question_options o"
            f"  WHERE o.question_version_id=(SELECT latest_version_id FROM questions WHERE id='{qid}')"
            ")) "
            f"WHERE a.id=(SELECT latest_annotation_id FROM questions WHERE id='{qid}');"
        )
    return stmts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    args = ap.parse_args()

    stmts = build_statements()
    body = "\n".join(stmts)
    sql = "BEGIN;\n" + body + ("\nCOMMIT;" if args.commit else "\nROLLBACK;")

    r = subprocess.run(DB + ["-v", "ON_ERROR_STOP=1"], input=sql, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"transaction failed (rolled back):\n{r.stderr}")
    print(r.stdout.strip()[-400:])
    print(f"\n{len(stmts)} statements {'COMMITTED' if args.commit else 'rolled back (dry run)'}")


if __name__ == "__main__":
    main()
