"""Pass 3 prompt — sentence span annotation for grammar practice highlighting.

Two-layer caching mirrors annotate_prompt.py:
  - @lru_cache(maxsize=1): Python-layer, prevents string reconstruction per process
  - system_static block: sent with cache_control:ephemeral for Anthropic server-side caching
  - system_dynamic block: short instructions, sent fresh each call

Split: static = vocab tables + 5 examples (~90% of tokens, never changes)
       dynamic = role + output rules (short, logically "instructions")
"""
from functools import lru_cache


# ──────────────────────────────────────────────────────────────────────────────
# Static block — vocabulary tables + annotated examples
# Sent with cache_control:ephemeral so Anthropic caches it server-side
# ──────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def build_span_prompt_static() -> str:
    return """
=== ANATOMY KEY VOCABULARY ===

Structural elements — what a span IS:

  independent_clause    — a complete clause with finite verb; can stand as a sentence
  subject               — the noun phrase that the main verb agrees with
  predicate             — everything in the clause after the subject
  main_verb             — the finite verb (or the blank that represents it)
  verb_phrase           — auxiliary + main verb together
  object                — direct or indirect object of the main verb
  complement            — predicate adjective or noun after a linking verb
  subordinate_clause    — a clause that cannot stand alone (begins with subordinating conj)
  adverbial_clause      — subordinate clause that modifies the main verb (time, cause, condition)
  relative_clause       — clause introduced by which/who/whom/whose modifying a noun
  restrictive_clause    — relative clause essential to meaning (no commas)
  nonrestrictive_clause — relative clause non-essential to meaning (set off by commas)
  noun_clause           — clause that functions as a noun (subject, object, complement)
  prepositional_phrase  — preposition + noun phrase (common SVA distractor)
  participial_phrase    — phrase beginning with -ing or -ed participle (modifies a noun)
  infinitive_phrase     — phrase beginning with "to" + verb
  gerund_phrase         — phrase beginning with -ing noun form
  absolute_phrase       — noun + participial phrase, grammatically independent of main clause
  adverbial_phrase      — phrase that modifies verb/adjective/adverb
  noun_phrase           — a noun and its modifiers (not a full clause)
  modifier              — any word, phrase, or clause that describes another element
  appositive            — noun phrase that renames the noun immediately before it
  nonrestrictive_element — parenthetical modifier set off by commas/dashes/parentheses
  introductory_element  — any element before the main clause (adverbial clause, PP, participle)
  parenthetical         — interrupting phrase set off by commas/dashes (could be removed)
  series_item           — one element in a list of parallel items
  subordinating_conj    — word that introduces a subordinate clause (although, because, etc.)
  coordinating_conjunction — FANBOYS word joining parallel elements (for, and, nor, but, or, yet, so)
  correlative_conjunction — paired conjunctions (not only…but also, either…or, both…and)
  conjunctive_adverb    — transition adverb used after semicolon (however, therefore, etc.)
  transition_word       — the blank slot when testing transition/conjunctive-adverb choice
  pronoun               — pronoun (or the blank slot when testing pronoun choice)
  antecedent            — the noun a pronoun refers back to
  determiner            — article/determiner (or blank slot when testing article/determiner)
  punctuation_mark      — a comma, semicolon, colon, or dash (or blank slot for punctuation)


=== CONCEPT KEY VOCABULARY ===

Grammar concepts — why a span MATTERS for this question:

  Sentence boundary:   sentence_fragment, comma_splice, run_on_sentence, sentence_boundary
  Agreement:           subject_verb_agreement, pronoun_antecedent_agreement, noun_countability, determiners_articles
  Pronoun:             pronoun_case, pronoun_clarity
  Verb form:           verb_tense_consistency, verb_form, voice_active_passive, negation
  Modifier:            modifier_placement, absolute_phrase, comparative_structures,
                       illogical_comparison, adjective_adverb_distinction,
                       logical_predication, relative_pronouns
  Punctuation:         punctuation_comma, colon_dash_use, semicolon_use,
                       conjunctive_adverb_usage, apostrophe_use, possessive_contraction,
                       appositive_punctuation, hyphen_usage, quotation_punctuation,
                       unnecessary_internal_punctuation, end_punctuation_question_statement
  Parallel structure:  parallel_structure, elliptical_constructions, conjunction_usage
  Expression of ideas: redundancy_concision, precision_word_choice, register_style_consistency,
                       logical_relationships, emphasis_meaning_shifts, data_interpretation_claims,
                       transition_logic, commonly_confused_words, preposition_idiom
  Syntactic traps:     nearest_noun_attraction, garden_path, early_clause_anchor,
                       nominalization_obscures_subject, interruption_breaks_subject_verb,
                       long_distance_dependency, pronoun_ambiguity, scope_of_negation,
                       modifier_attachment_ambiguity, presupposition_trap,
                       temporal_sequence_ambiguity


=== BLANK-SLOT ANATOMY MAPPING ===

Use this table to assign anatomy to a blank (_______) token:

  grammar_focus_key                  → blank anatomy
  ─────────────────────────────────────────────────────
  verb_tense_consistency             → ["main_verb"]
  verb_form                          → ["main_verb"]
  subject_verb_agreement             → ["main_verb"]
  voice_active_passive               → ["main_verb"]
  transition_logic                   → ["transition_word", "conjunctive_adverb"]
  conjunctive_adverb_usage           → ["transition_word", "conjunctive_adverb"]
  logical_relationships              → ["transition_word", "conjunctive_adverb"]
  pronoun_antecedent_agreement       → ["pronoun"]
  pronoun_case                       → ["pronoun"]
  pronoun_clarity                    → ["pronoun"]
  determiners_articles               → ["determiner"]
  noun_countability                  → ["determiner"]
  punctuation_comma                  → ["punctuation_mark"]
  semicolon_use                      → ["punctuation_mark"]
  colon_dash_use                     → ["punctuation_mark"]
  apostrophe_use                     → ["punctuation_mark"]
  appositive_punctuation             → ["punctuation_mark"]
  (all other keys)                   → use only anatomy keys from the ANATOMY KEY VOCABULARY above; "verb_form" and "verb_tense_consistency" are CONCEPT keys, not anatomy keys — never put them in anatomy


=== ABSOLUTE PHRASE vs. PARTICIPIAL PHRASE DISAMBIGUATION ===

Absolute phrase: noun + participle, grammatically free from the main clause.
  "Her hands trembling, she opened the envelope." → "Her hands trembling" = absolute_phrase
  (Subject of the absolute phrase is DIFFERENT from the subject of the main clause)

Participial phrase: participle modifying a noun in the main clause.
  "Trembling, she opened the envelope." → "Trembling" = participial_phrase
  (No separate noun; participle agrees with the main clause subject)

Tag the whole phrase as a single token in both cases.


=== ANNOTATED EXAMPLES ===

--- Example 1: Subject-Verb Agreement with PP Distractor ---
Passage: "The number of students enrolled in the program _______  dramatically over the past decade."
grammar_focus_key: subject_verb_agreement
syntactic_trap_key: nearest_noun_attraction

Output:
[
  {"text": "The number", "anatomy": ["subject"], "concept_tags": ["subject_verb_agreement"], "is_blank": false},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "of students", "anatomy": ["prepositional_phrase"], "concept_tags": ["subject_verb_agreement", "nearest_noun_attraction"], "is_blank": false},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "enrolled in the program", "anatomy": ["participial_phrase"], "concept_tags": ["subject_verb_agreement"], "is_blank": false},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "_______", "anatomy": ["main_verb"], "concept_tags": ["subject_verb_agreement"], "is_blank": true},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "dramatically", "anatomy": ["modifier"], "concept_tags": [], "is_blank": false},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "over the past decade", "anatomy": ["prepositional_phrase"], "concept_tags": [], "is_blank": false},
  {"text": ".", "anatomy": [], "concept_tags": [], "is_blank": false}
]

--- Example 2: Verb Tense Consistency ---
Passage: "By the time the results _______ published, the team had already moved on to the next phase."
grammar_focus_key: verb_tense_consistency

Output:
[
  {"text": "By the time", "anatomy": ["subordinating_conj", "adverbial_clause"], "concept_tags": ["verb_tense_consistency"], "is_blank": false},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "the results", "anatomy": ["subject"], "concept_tags": ["verb_tense_consistency"], "is_blank": false},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "_______", "anatomy": ["main_verb"], "concept_tags": ["verb_tense_consistency"], "is_blank": true},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "published,", "anatomy": ["verb_phrase"], "concept_tags": ["verb_tense_consistency"], "is_blank": false},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "the team", "anatomy": ["subject"], "concept_tags": [], "is_blank": false},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "had already moved on", "anatomy": ["main_verb"], "concept_tags": ["verb_tense_consistency"], "is_blank": false},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "to the next phase", "anatomy": ["prepositional_phrase"], "concept_tags": [], "is_blank": false},
  {"text": ".", "anatomy": [], "concept_tags": [], "is_blank": false}
]

--- Example 3: Transition Logic (two sentences) ---
Passage: "The expedition members reported extreme fatigue. _______, they pressed on toward the summit."
grammar_focus_key: transition_logic

Output:
[
  {"text": "The expedition members", "anatomy": ["subject"], "concept_tags": [], "is_blank": false},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "reported", "anatomy": ["main_verb"], "concept_tags": [], "is_blank": false},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "extreme fatigue", "anatomy": ["object"], "concept_tags": [], "is_blank": false},
  {"text": ".", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "_______,", "anatomy": ["transition_word", "conjunctive_adverb"], "concept_tags": ["transition_logic", "conjunctive_adverb_usage"], "is_blank": true},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "they", "anatomy": ["subject"], "concept_tags": [], "is_blank": false},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "pressed on", "anatomy": ["main_verb"], "concept_tags": [], "is_blank": false},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "toward the summit", "anatomy": ["prepositional_phrase"], "concept_tags": [], "is_blank": false},
  {"text": ".", "anatomy": [], "concept_tags": [], "is_blank": false}
]

--- Example 4: Pronoun Agreement ---
Passage: "Each of the researchers submitted _______ final report by the deadline."
grammar_focus_key: pronoun_antecedent_agreement

Output:
[
  {"text": "Each", "anatomy": ["subject", "antecedent"], "concept_tags": ["pronoun_antecedent_agreement"], "is_blank": false},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "of the researchers", "anatomy": ["prepositional_phrase"], "concept_tags": ["pronoun_antecedent_agreement", "nearest_noun_attraction"], "is_blank": false},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "submitted", "anatomy": ["main_verb"], "concept_tags": [], "is_blank": false},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "_______", "anatomy": ["pronoun"], "concept_tags": ["pronoun_antecedent_agreement"], "is_blank": true},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "final report", "anatomy": ["object"], "concept_tags": [], "is_blank": false},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "by the deadline", "anatomy": ["prepositional_phrase"], "concept_tags": [], "is_blank": false},
  {"text": ".", "anatomy": [], "concept_tags": [], "is_blank": false}
]

--- Example 5: Comma Mechanics — introductory element + appositive ---
Passage: "A renowned marine biologist_______ Dr. Chen spent decades studying deep-sea ecosystems."
grammar_focus_key: punctuation_comma

Output:
[
  {"text": "A renowned marine biologist", "anatomy": ["introductory_element", "appositive"], "concept_tags": ["punctuation_comma", "appositive_punctuation"], "is_blank": false},
  {"text": "_______", "anatomy": ["punctuation_mark"], "concept_tags": ["punctuation_comma", "appositive_punctuation"], "is_blank": true},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "Dr. Chen", "anatomy": ["subject"], "concept_tags": ["punctuation_comma"], "is_blank": false},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "spent", "anatomy": ["main_verb"], "concept_tags": [], "is_blank": false},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "decades", "anatomy": ["object"], "concept_tags": [], "is_blank": false},
  {"text": " ", "anatomy": [], "concept_tags": [], "is_blank": false},
  {"text": "studying deep-sea ecosystems", "anatomy": ["participial_phrase"], "concept_tags": [], "is_blank": false},
  {"text": ".", "anatomy": [], "concept_tags": [], "is_blank": false}
]
"""


# ──────────────────────────────────────────────────────────────────────────────
# Dynamic block — role definition + output rules
# Short; sent fresh each call alongside the cached static block
# ──────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def build_span_prompt_dynamic() -> str:
    return """You are a DSAT sentence anatomy annotator. Given a passage from an official SAT grammar question and its grammar taxonomy annotation, you tokenize the passage into grammatical-unit spans and tag each span with anatomy and grammar concept labels.

=== PHRASE-LEVEL GROUPING RULE ===
Group tokens by grammatical unit, NOT by individual word. A prepositional phrase like "of students" is ONE token, not three. A subject like "The number" is ONE token. Only split at clause boundaries, phrase boundaries, or where the grammar_focus_key requires distinguishing adjacent elements. Whitespace between units must be preserved as separate " " tokens to maintain the concatenation invariant.

=== OUTPUT FORMAT ===
Return a JSON array ONLY. No prose before or after the array.
Each element: {"text": str, "anatomy": [str], "concept_tags": [str], "is_blank": bool}
Whitespace between tokens must appear as separate " " tokens.

=== CONCATENATION INVARIANT ===
The concatenation of all "text" values must exactly equal the input passage text, character for character. Whitespace between units must appear as separate tokens. Do not merge or drop any characters. Do not add any characters. Count your characters.

=== MULTI-SENTENCE RULE ===
If the passage contains two sentences, annotate each sentence's tokens separately. Never merge both sentences into a single token. The transition blank in sentence 2 belongs to sentence 2's token sequence.

=== BLANK SLOT RULE ===
Identify _______ as a blank token (is_blank: true). Assign the blank's anatomy using the focus_key mapping table in the reference block above. Do not tag a blank as main_verb if the question tests a transition word or pronoun.

=== DUAL-TAGGING RULE ===
A single span may carry both anatomy and concept tags. Example: "of students" in an SVA question gets anatomy=["prepositional_phrase"] AND concept_tags=["subject_verb_agreement", "nearest_noun_attraction"].

=== PUNCTUATION TOKEN RULE ===
For punctuation questions (punctuation_comma, semicolon_use, colon_dash_use, etc.), tokenize the comma/semicolon/colon/dash itself as a separate token with anatomy=["punctuation_mark"] and the relevant concept_tag. If the blank IS the punctuation mark, tokenize it as is_blank=true with anatomy=["punctuation_mark"].
"""


def build_span_system_prompt() -> str:
    """Combine static + dynamic into a single system prompt (for providers without split caching)."""
    return build_span_prompt_static() + "\n" + build_span_prompt_dynamic()


def build_span_user_message(
    passage_text: str,
    grammar_focus_key: str | None,
    grammar_role_key: str | None,
    syntactic_trap_key: str | None,
    secondary_keys: list[str],
) -> str:
    lines = [
        f'Passage text: "{passage_text}"',
        f'grammar_focus_key: "{grammar_focus_key or ""}"',
        f'grammar_role_key: "{grammar_role_key or ""}"',
        f'syntactic_trap_key: "{syntactic_trap_key or ""}"',
        f'secondary_grammar_focus_keys: {secondary_keys}',
        "",
        "Tokenize this passage into grammatical-unit spans. Return a JSON array only.",
    ]
    return "\n".join(lines)


def parse_llm_span_response(raw: str) -> list[dict]:
    """Strip markdown fences and parse JSON. Raises ValueError on failure."""
    import json
    import re
    text = raw.strip()
    # Strip ```json ... ``` fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM response is not valid JSON: {exc}\nRaw: {raw[:200]!r}") from exc
    if not isinstance(result, list):
        raise ValueError(f"LLM response is not a JSON array. Got: {type(result).__name__}")
    return result
