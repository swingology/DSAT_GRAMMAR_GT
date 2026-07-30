"""Pass 1 prompt — extracts structured question data from raw text."""

from app.models.ontology import STEM_TYPE_KEYS, STIMULUS_MODE_KEYS


# Known non-canonical stem_type_key aliases the extraction LLM has emitted in
# practice (e.g. "analyze_text_structure", "retrieve_detail", "compare_texts").
# Map them to canonical STEM_TYPE_KEYS so Pass 2 routing (_detect_domain) matches
# a real domain bucket instead of falling through to "unknown" + grammar Part D.
# This is a safety net behind the controlled-vocabulary prompt constraint; if a
# stem isn't canonical and has no alias, canonicalize_stem returns None and the
# caller leaves it (routes to "unknown" → Pass 2 post-processor still classifies).
_STEM_ALIASES = {
    # cross-text / structure / function
    "compare_texts": "choose_cross_text_connection",
    "compare_text": "choose_text_relationship",
    "analyze_text_structure": "choose_structure_description",
    "analyze_structure": "choose_structure_description",
    "describe_structure": "choose_structure_description",
    "analyze_function_of_sentence": "choose_sentence_function",
    "analyze_function_of_phrase": "choose_sentence_function",
    "function_of_underlined": "choose_sentence_function",
    "function_of_part": "choose_sentence_function",
    "choose_function": "choose_sentence_function",
    # details / evidence
    "retrieve_detail": "choose_detail",
    "retrieve_information": "choose_detail",
    "support_claim": "choose_best_support",
    "support_claim_with_evidence": "choose_best_support",
    "support_idea": "choose_best_support",
    # synthesis / transitions / conventions
    "synthesize_notes": "choose_best_notes_synthesis",
    "synthesize_information_from_notes": "choose_best_notes_synthesis",
    "rhetorical_synthesis": "choose_best_notes_synthesis",
    "logical_transition": "choose_best_transition",
    "choose_transition": "choose_best_transition",
    "choose_logical_transition": "choose_best_transition",
    "choose_conjunction": "choose_best_transition",
    "punctuation_convention": "conform_to_standard_english",
    "grammar_convention": "conform_to_standard_english",
    "choose_grammatically_correct_form": "conform_to_standard_english",
    "conventions_of_english": "conform_to_standard_english",
    "fix_punctuation": "conform_to_standard_english",
    "fix_sentence_boundary": "conform_to_standard_english",
    "no_change": "conform_to_standard_english",
    # inference / completion
    "inference": "choose_best_inference",
    "infer_author_opinion": "choose_best_inference",
    "infer_character": "choose_best_inference",
    "analyze_argument": "choose_best_inference",
    "complete_the_implication": "most_logically_completes",
    "complete_the_hypothesis": "most_logically_completes",
    "complete_the_argument": "most_logically_completes",
    "use_data_to_complete_statement": "choose_best_completion_from_data",
    # vocab / purpose / quantitative / cross-text variants
    "define_word_in_context": "choose_words_in_context",
    "vocabulary_in_context": "choose_words_in_context",
    "state_main_purpose": "choose_main_purpose",
    "identify_main_purpose": "choose_main_purpose",
    "state_main_idea": "choose_main_idea",
    "interpret_graph": "choose_command_of_evidence_quantitative",
    "interpret_data": "choose_command_of_evidence_quantitative",
    "present_methods": "compare_contributions",
    "emphasize_similarity": "choose_agreement_across_texts",
    "compare_hypotheses": "choose_difference_across_texts",
}

_STIMULUS_ALIASES = {
    "paired_prose": "prose_paired",
    "single_prose": "prose_single",
    "prose_with_table": "prose_plus_table",
    "prose_with_graph": "prose_plus_graph",
    "prose_and_table": "prose_plus_table",
    "prose_and_graph": "prose_plus_graph",
    "table": "prose_plus_table",
    "graph": "prose_plus_graph",
    "sentence": "sentence_only",
    "excerpt": "passage_excerpt",
    "passage": "passage_excerpt",
}


def canonicalize_stem(stem: str | None) -> str | None:
    """Return a canonical STEM_TYPE_KEYS value for ``stem``, or None if none fits.

    Pass-through if already canonical; alias-mapped if a known non-canonical
    alias; None if unknown (caller leaves the value untouched).
    """
    if not stem:
        return stem
    s = stem.strip().lower()
    if s in STEM_TYPE_KEYS:
        return s
    return _STEM_ALIASES.get(s)


def canonicalize_stimulus_mode(mode: str | None) -> str | None:
    """Return a canonical STIMULUS_MODE_KEYS value for ``mode``, or None."""
    if not mode:
        return mode
    m = mode.strip().lower()
    if m in STIMULUS_MODE_KEYS:
        return m
    return _STIMULUS_ALIASES.get(m)


def _allowed_vocab_block() -> str:
    return (
        "=== ALLOWED stem_type_key VALUES (choose EXACTLY one, verbatim; "
        "never invent a synonym or variant) ===\n  "
        + ", ".join(STEM_TYPE_KEYS)
        + "\n\n=== ALLOWED stimulus_mode_key VALUES (choose EXACTLY one, verbatim) ===\n  "
        + ", ".join(STIMULUS_MODE_KEYS)
    )


_EXTRACT_SYSTEM_BASE = """You are a DSAT question extraction specialist. Your job is to extract ALL questions from raw text extracted from SAT practice material.

CRITICAL: Extract EVERY numbered question in the text. A single SAT module contains 27–33 questions. Do not stop after the first question — scan the entire text and include all of them in the "questions" array.

When a passage is shared across multiple questions, use the same passage_text for each of those questions.

You must output valid JSON matching this schema:
{
  "passage_text": "The shared passage text, or null if no passage",
  "paired_passage_text": null,
  "source_release_year": "2024 or 2025 or null — use the value from source metadata if provided",
  "source_test_name": "e.g. Bluebook Practice Test 1, Linear SAT Practice Test 1, or null — use the value from source metadata if provided",
  "source_exam_code": "e.g. PT1, PT4, PT11, or null — use the value from the source metadata if provided",
  "source_subject_code": "verbal or math or null",
  "source_section_code": "01 or 02 or null",
  "source_module_code": "01 or 02 or null",
  "questions": [
    {
      "question_text": "The prompt/stem text",
      "source_question_number": "1 or null",
      "passage_text": "The passage for this question (Text 1 for cross-text questions), or null",
      "paired_passage_text": "For cross-text (Text 1 / Text 2) questions ONLY: put Text 2 here. Null for all other question types.",
      "options": [
        {"label": "A", "text": "option A text"},
        {"label": "B", "text": "option B text"},
        {"label": "C", "text": "option C text"},
        {"label": "D", "text": "option D text"}
      ],
      "correct_option_label": "A or B or C or D",
      "stimulus_mode_key": "one of the allowed stimulus_mode_key values listed below (verbatim)",
      "stem_type_key": "one of the allowed stem_type_key values listed below (verbatim)",
      "stimulus_assets": [
        {
          "type": "table, chart, graph, or figure",
          "title": "optional title visible in the source",
          "structured_data": {
            "comment": "For tables: {headers: [...], rows: [[...], ...]}. For charts: {x_label, y_label, series: [{label, data}]}. For figures: {description}."
          },
          "render_hints": {
            "chart_type": "bar, line, pie, scatter, table, or figure",
            "x_label": "axis label or null",
            "y_label": "axis label or null"
          }
        }
      ]
    }
  ],
  "table_data": null,
  "graph_data": null
}

Rules:
- Always produce exactly 4 options labeled A, B, C, D per question
- CONTROLLED VOCABULARY — stem_type_key and stimulus_mode_key MUST be chosen verbatim from the allowed-values lists below. Never invent a synonym, abbreviation, or descriptive variant (e.g. do NOT use "compare_texts", "analyze_text_structure", "retrieve_detail", "support_claim", or "synthesize_notes" — use the corresponding canonical key from the list). If you are unsure which canonical key fits, pick the closest one from the list rather than inventing a new label.
- QUESTION NUMBERING — read carefully:
  • source_question_number MUST be the literal printed number shown next to that
    question in the source text. Copy it; do not compute or guess it.
  • A verbal module has at most 33 questions (numbered 1–33); a math module has
    at most 22 (numbered 1–22). NEVER emit a number above the module maximum.
  • Numbers must be unique and form a contiguous run with no gaps.
  • If a question has no visible printed number, set source_question_number to
    null — do NOT invent a number to fill the sequence.
  • Do not renumber questions based on their position in your output array.
- Identify the correct answer from the answer key, a circled/checked/highlighted/underlined option, bold formatting, or any other visual marker in the source. If NO answer marker is visible in the source (question-only documents with no selection indicated), set correct_option_label to null — do NOT guess
- Preserve the original wording as closely as possible
- PASSAGE TEXT — include the full passage exactly as presented in the source:
  • If there is an introductory or attribution sentence before the passage body
    (e.g. "The following text is adapted from ...", "The passage below is excerpted from ..."),
    include it as the first line(s) of passage_text — do NOT omit it.
  • passage_text should be the complete block: intro/attribution sentence(s) + passage body.
  • If no passage, set passage_text to null
- CROSS-TEXT (Text 1 / Text 2) QUESTIONS — when a question refers to two labeled texts:
  • Put the full Text 1 block in passage_text for that question
  • Put the full Text 2 block in paired_passage_text for that question
  • Set stimulus_mode_key to "prose_paired"
  • Set stem_type_key to "choose_cross_text_connection"
  • paired_passage_text must NEVER be null for these questions
- For a single question, return a questions array with one element
- If a question is accompanied by a table, chart, graph, or figure, populate stimulus_assets for that question with one entry per distinct visual element. If there are no visual elements, set stimulus_assets to []
- For tables: extract headers and rows into structured_data. For charts/graphs: extract axis labels and data series into structured_data. For figures: provide a text description
- Output ONLY valid JSON, no markdown fences
"""

# Kept as a module-level string for backward compatibility with callers/tests
# that reference EXTRACT_SYSTEM_PROMPT directly. Built by plain concatenation
# (not str.format) so the JSON schema braces need no escaping.
EXTRACT_SYSTEM_PROMPT = _EXTRACT_SYSTEM_BASE + "\n" + _allowed_vocab_block()


def build_vision_extract_prompt(source_metadata: dict = None) -> tuple[str, str]:
    """Build prompts for vision-fused extraction (Ollama VLM path, Option B).

    The model reads directly from image content — no raw_text in the user message.
    Same JSON schema is expected in the response.
    """
    source_hints = ""
    if source_metadata:
        hints = [f"{k}: {v}" for k, v in source_metadata.items() if v]
        source_hints = "\nSource metadata:\n" + "\n".join(hints) if hints else ""

    user = (
        f"Extract ALL questions from the image(s) above. "
        f"Follow the JSON schema exactly. Include every numbered question.{source_hints}"
    )
    return EXTRACT_SYSTEM_PROMPT, user


def build_extract_prompt(raw_text: str, source_metadata: dict = None) -> tuple[str, str]:
    """Build system and user prompts for Pass 1 extraction."""
    source_hints = ""
    if source_metadata:
        hints = [f"{k}: {v}" for k, v in source_metadata.items() if v]
        source_hints = "\nSource metadata:\n" + "\n".join(hints) if hints else ""

    user = f"""Extract ALL questions from the following raw text. Include every numbered question you find — do not stop early.{source_hints}

---
{raw_text}
---"""
    return EXTRACT_SYSTEM_PROMPT, user