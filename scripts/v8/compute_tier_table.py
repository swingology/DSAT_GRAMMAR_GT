"""Tier each grammar_focus_key by PT evidence count.

Tier A: >= 5 PT examples (full 3 PT-cited sub-patterns achievable)
Tier B: 1-4 PT examples (mix PT + web, minimum 1 PT)
Tier C: 0 PT examples (web-cited only, NO PT EVIDENCE marker)
"""
import json
from pathlib import Path

EVIDENCE = Path("analysis/v8/focus_evidence")
OUT = Path("analysis/v8/tier_table.json")

V7_FOCUS_KEYS = [
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
    "redundancy_concision", "precision_word_choice",
    "register_style_consistency", "logical_relationships",
    "emphasis_meaning_shifts", "data_interpretation_claims", "transition_logic",
    "commonly_confused_words", "preposition_idiom",
]


def main() -> int:
    table = {}
    for key in V7_FOCUS_KEYS:
        ev_file = EVIDENCE / f"{key}.json"
        if ev_file.exists():
            count = len(json.loads(ev_file.read_text()))
        else:
            count = 0
        if count >= 5:
            tier = "A"
        elif count >= 1:
            tier = "B"
        else:
            tier = "C"
        table[key] = {"pt_examples": count, "tier": tier}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(table, indent=2, sort_keys=True))

    by_tier: dict[str, int] = {"A": 0, "B": 0, "C": 0}
    for v in table.values():
        by_tier[v["tier"]] += 1
    print(f"Tier A (>=5 PT examples): {by_tier['A']} focus keys")
    print(f"Tier B (1-4 PT examples): {by_tier['B']} focus keys")
    print(f"Tier C (0 PT examples):   {by_tier['C']} focus keys")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
