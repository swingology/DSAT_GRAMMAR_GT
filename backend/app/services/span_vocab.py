"""Single source of truth for all approved span annotation key sets.

Imported by span_validator, span_label, and span_prompt.
"""

ANATOMY_KEYS: frozenset[str] = frozenset({
    # Core clause / predicate
    "independent_clause", "subject", "predicate", "main_verb",
    "verb_phrase", "object", "complement",
    # Subordinate clause types
    "subordinate_clause", "adverbial_clause", "relative_clause",
    "restrictive_clause", "nonrestrictive_clause", "noun_clause",
    # Phrases
    "prepositional_phrase", "participial_phrase", "infinitive_phrase",
    "gerund_phrase", "absolute_phrase", "adverbial_phrase", "noun_phrase",
    # Modifiers
    "modifier", "appositive", "nonrestrictive_element",
    # Position / punctuation structures
    "introductory_element", "parenthetical", "series_item",
    # Conjunctions / connectors
    "subordinating_conj", "coordinating_conjunction", "correlative_conjunction",
    "conjunctive_adverb", "transition_word",
    # Pronouns / reference
    "pronoun", "antecedent",
    # Blank-slot only
    "determiner", "punctuation_mark",
})

CONCEPT_KEYS: frozenset[str] = frozenset({
    # D.2.1 Sentence boundary
    "sentence_fragment", "comma_splice", "run_on_sentence", "sentence_boundary",
    # D.2.2 Agreement
    "subject_verb_agreement", "pronoun_antecedent_agreement",
    "noun_countability", "determiners_articles",
    # D.2.3 Pronoun
    "pronoun_case", "pronoun_clarity",
    # D.2.4 Verb form
    "verb_tense_consistency", "verb_form", "voice_active_passive", "negation",
    # D.2.5 Modifier
    "modifier_placement", "absolute_phrase", "comparative_structures",
    "illogical_comparison", "adjective_adverb_distinction",
    "logical_predication", "relative_pronouns",
    # D.2.6 Punctuation
    "punctuation_comma", "colon_dash_use", "semicolon_use",
    "conjunctive_adverb_usage", "apostrophe_use", "possessive_contraction",
    "appositive_punctuation", "hyphen_usage", "quotation_punctuation",
    "unnecessary_internal_punctuation", "end_punctuation_question_statement",
    # D.2.7 Parallel structure
    "parallel_structure", "elliptical_constructions", "conjunction_usage",
    # D.2.8 Expression of ideas
    "redundancy_concision", "precision_word_choice", "register_style_consistency",
    "logical_relationships", "emphasis_meaning_shifts", "data_interpretation_claims",
    "transition_logic", "commonly_confused_words", "preposition_idiom",
    # D.5 Syntactic traps
    "nearest_noun_attraction", "garden_path", "early_clause_anchor",
    "nominalization_obscures_subject", "interruption_breaks_subject_verb",
    "long_distance_dependency", "pronoun_ambiguity", "scope_of_negation",
    "modifier_attachment_ambiguity", "presupposition_trap",
    "temporal_sequence_ambiguity",
})

# Maps grammar_focus_key → anatomy tags to assign the blank token
BLANK_ANATOMY_MAP: dict[str, list[str]] = {
    # Verb keys
    "verb_tense_consistency":       ["main_verb", "verb_form", "verb_tense_consistency"],
    "verb_form":                    ["main_verb", "verb_form", "verb_tense_consistency"],
    "subject_verb_agreement":       ["main_verb", "verb_form", "verb_tense_consistency"],
    "voice_active_passive":         ["main_verb", "verb_form", "verb_tense_consistency"],
    # Transition keys
    "transition_logic":             ["transition_word", "conjunctive_adverb"],
    "conjunctive_adverb_usage":     ["transition_word", "conjunctive_adverb"],
    "logical_relationships":        ["transition_word", "conjunctive_adverb"],
    # Pronoun keys
    "pronoun_antecedent_agreement": ["pronoun"],
    "pronoun_case":                 ["pronoun"],
    "pronoun_clarity":              ["pronoun"],
    # Determiner keys
    "determiners_articles":         ["determiner"],
    "noun_countability":            ["determiner"],
    # Punctuation keys
    "punctuation_comma":            ["punctuation_mark"],
    "semicolon_use":                ["punctuation_mark"],
    "colon_dash_use":               ["punctuation_mark"],
    "apostrophe_use":               ["punctuation_mark"],
    "appositive_punctuation":       ["punctuation_mark"],
}

BLANK_ANATOMY_DEFAULT: list[str] = ["main_verb", "verb_form", "verb_tense_consistency"]


def blank_anatomy_for(grammar_focus_key: str | None) -> list[str]:
    return BLANK_ANATOMY_MAP.get(grammar_focus_key or "", BLANK_ANATOMY_DEFAULT)
