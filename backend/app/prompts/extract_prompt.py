"""Pass 1 prompt — extracts structured question data from raw text."""


EXTRACT_SYSTEM_PROMPT = """You are a DSAT question extraction specialist. Your job is to extract structured question data from raw text extracted from SAT practice material.

You must output valid JSON matching this schema:
{
  "question_text": "The prompt/stem text",
  "passage_text": "The passage or null",
  "paired_passage_text": null,
  "options": [
    {"label": "A", "text": "option A text"},
    {"label": "B", "text": "option B text"},
    {"label": "C", "text": "option C text"},
    {"label": "D", "text": "option D text"}
  ],
  "correct_option_label": "A or B or C or D",
  "source_exam_code": "PT4 or null",
  "source_module_code": "M1 or null",
  "source_question_number": 1 or null,
  "stimulus_mode_key": "sentence_only or passage_excerpt etc.",
  "stem_type_key": "complete_the_text or choose_main_idea etc.",
  "table_data": null,
  "graph_data": null
}

Rules:
- Always produce exactly 4 options labeled A, B, C, D
- Identify the correct answer from the answer key or context
- Preserve the original wording as closely as possible
- If no passage, set passage_text to null
- Output ONLY valid JSON, no markdown fences"""


def build_extract_prompt(raw_text: str, source_metadata: dict = None) -> tuple[str, str]:
    """Build system and user prompts for Pass 1 extraction."""
    source_hints = ""
    if source_metadata:
        hints = [f"{k}: {v}" for k, v in source_metadata.items() if v]
        source_hints = "\nSource metadata:\n" + "\n".join(hints) if hints else ""

    user = f"""Extract the question data from the following raw text:{source_hints}

---
{raw_text}
---"""
    return EXTRACT_SYSTEM_PROMPT, user