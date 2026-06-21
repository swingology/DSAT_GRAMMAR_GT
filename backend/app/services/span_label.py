"""Generate a human-readable label for a passage span annotation.

Label format:  "<Prefix>: <anatomy_elem1> + <anatomy_elem2> ... [trap_note]"
Max 4 anatomy elements; trap keys appended in brackets.
"""

PREFIX_MAP: dict[str, str] = {
    "subject_verb_agreement":            "SVA",
    "verb_tense_consistency":            "Verb tense",
    "verb_form":                         "Verb form",
    "voice_active_passive":              "Active/passive voice",
    "transition_logic":                  "Transition logic",
    "pronoun_antecedent_agreement":      "Pronoun agreement",
    "pronoun_case":                      "Pronoun case",
    "pronoun_clarity":                   "Pronoun clarity",
    "modifier_placement":                "Modifier placement",
    "absolute_phrase":                   "Absolute phrase",
    "comparative_structures":            "Comparative structure",
    "illogical_comparison":              "Illogical comparison",
    "adjective_adverb_distinction":      "Adjective/adverb",
    "logical_predication":               "Logical predication",
    "relative_pronouns":                 "Relative pronoun",
    "punctuation_comma":                 "Comma mechanics",
    "semicolon_use":                     "Semicolon",
    "colon_dash_use":                    "Colon/dash",
    "conjunctive_adverb_usage":          "Conjunctive adverb",
    "apostrophe_use":                    "Apostrophe",
    "possessive_contraction":            "Possessive/contraction",
    "appositive_punctuation":            "Appositive punctuation",
    "hyphen_usage":                      "Hyphen",
    "quotation_punctuation":             "Quotation punctuation",
    "unnecessary_internal_punctuation":  "Unnecessary punctuation",
    "end_punctuation_question_statement": "End punctuation",
    "parallel_structure":                "Parallel structure",
    "elliptical_constructions":          "Elliptical construction",
    "conjunction_usage":                 "Conjunction choice",
    "sentence_fragment":                 "Fragment",
    "comma_splice":                      "Comma splice",
    "run_on_sentence":                   "Run-on",
    "sentence_boundary":                 "Sentence boundary",
    "noun_countability":                 "Countability",
    "determiners_articles":              "Determiner/article",
    "negation":                          "Negation",
    "redundancy_concision":              "Concision",
    "precision_word_choice":             "Word choice",
    "register_style_consistency":        "Register",
    "logical_relationships":             "Logical relationship",
    "emphasis_meaning_shifts":           "Emphasis/meaning",
    "data_interpretation_claims":        "Data claim",
    "commonly_confused_words":           "Confused words",
    "preposition_idiom":                 "Preposition idiom",
}

# Human-readable names for anatomy elements used in labels
_ANATOMY_LABELS: dict[str, str] = {
    "subject":               "subject",
    "prepositional_phrase":  "PP distractor",
    "main_verb":             "verb blank",
    "verb_form":             "verb blank",
    "transition_word":       "transition blank",
    "conjunctive_adverb":    "transition blank",
    "pronoun":               "pronoun blank",
    "determiner":            "determiner blank",
    "punctuation_mark":      "punctuation blank",
    "introductory_element":  "introductory element",
    "parenthetical":         "parenthetical",
    "appositive":            "appositive",
    "relative_clause":       "relative clause",
    "nonrestrictive_clause": "nonrestrictive clause",
    "participial_phrase":    "participial phrase",
    "absolute_phrase":       "absolute phrase",
    "independent_clause":    "independent clause",
    "subordinate_clause":    "subordinate clause",
    "series_item":           "series item",
    "antecedent":            "antecedent",
    "coordinating_conjunction": "coordinating conj",
    "subordinating_conj":    "subordinating conj",
}

# D.5 trap keys → bracket annotation
_TRAP_LABELS: dict[str, str] = {
    "nearest_noun_attraction":       "nearest noun attraction",
    "garden_path":                   "garden path",
    "early_clause_anchor":           "early clause anchor",
    "nominalization_obscures_subject": "nominalization",
    "interruption_breaks_subject_verb": "interruption",
    "long_distance_dependency":      "long-distance dependency",
    "pronoun_ambiguity":             "pronoun ambiguity",
    "scope_of_negation":             "scope of negation",
    "modifier_attachment_ambiguity": "modifier attachment",
    "presupposition_trap":           "presupposition trap",
    "temporal_sequence_ambiguity":   "temporal ambiguity",
}


def generate_span_label(
    grammar_focus_key: str | None,
    anatomy_present: list[str],
    concepts_present: list[str],
) -> str:
    # Determine prefix
    if grammar_focus_key and grammar_focus_key in PREFIX_MAP:
        prefix = PREFIX_MAP[grammar_focus_key]
    elif grammar_focus_key:
        prefix = grammar_focus_key.replace("_", " ").title()
    else:
        prefix = "Grammar"

    # Build anatomy suffix (up to 4 elements, using readable labels)
    anatomy_parts: list[str] = []
    seen: set[str] = set()
    for key in anatomy_present:
        label = _ANATOMY_LABELS.get(key)
        if label and label not in seen:
            seen.add(label)
            anatomy_parts.append(label)
        if len(anatomy_parts) == 4:
            break

    # Build trap note from D.5 keys in concepts_present
    trap_notes = [
        _TRAP_LABELS[k] for k in concepts_present if k in _TRAP_LABELS
    ]

    # Assemble
    if not anatomy_parts:
        result = prefix
    else:
        result = f"{prefix}: {' + '.join(anatomy_parts)}"

    if trap_notes:
        result = f"{result} [{', '.join(trap_notes)}]"

    return result[:80]
