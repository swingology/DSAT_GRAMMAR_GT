"""Pass 1 prompt — extracts structured question data from raw text."""


EXTRACT_SYSTEM_PROMPT = """You are a DSAT question extraction specialist. Your job is to extract ALL questions from raw text extracted from SAT practice material.

CRITICAL: Extract EVERY numbered question in the text. A single SAT module contains 27–33 questions. Do not stop after the first question — scan the entire text and include all of them in the "questions" array.

When a passage is shared across multiple questions, use the same passage_text for each of those questions.

You must output valid JSON matching this schema:
{
  "passage_text": "The shared passage text, or null if no passage",
  "paired_passage_text": null,
  "source_exam_code": "e.g. PT1, PT4, PT11, or null — use the value from the source metadata if provided",
  "source_subject_code": "verbal or math or null",
  "source_section_code": "01 or 02 or null",
  "source_module_code": "01 or 02 or null",
  "questions": [
    {
      "question_text": "The prompt/stem text",
      "source_question_number": 1 or null,
      "options": [
        {"label": "A", "text": "option A text"},
        {"label": "B", "text": "option B text"},
        {"label": "C", "text": "option C text"},
        {"label": "D", "text": "option D text"}
      ],
      "correct_option_label": "A or B or C or D",
      "stimulus_mode_key": "sentence_only or passage_excerpt etc.",
      "stem_type_key": "complete_the_text or choose_main_idea etc."
    }
  ],
  "table_data": null,
  "graph_data": null
}

Rules:
- Always produce exactly 4 options labeled A, B, C, D per question
- Identify the correct answer from the answer key or context
- Preserve the original wording as closely as possible
- If no passage, set passage_text to null
- For a single question, return a questions array with one element
- Output ONLY valid JSON, no markdown fences"""


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
