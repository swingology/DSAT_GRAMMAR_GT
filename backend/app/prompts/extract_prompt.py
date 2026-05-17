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
      "stem_type_key": "complete_the_text or choose_main_idea etc.",
      "stimulus_assets": [
        {
          "type": "table, chart, graph, or figure",
          "title": "optional title visible in the source",
          "structured_data": {
            "comment": "For tables: {headers: [...], rows: [[...], ...]}. For charts: {x_label: '...', y_label: '...', series: [{label: '...', data: [...]}]}. For figures: {description: '...'}."
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
- QUESTION NUMBERING — read carefully:
  • source_question_number MUST be the literal printed number shown next to that
    question in the source text. Copy it; do not compute or guess it.
  • A verbal module has at most 33 questions (numbered 1–33); a math module has
    at most 22 (numbered 1–22). NEVER emit a number above the module maximum.
  • Numbers must be unique and form a contiguous run with no gaps.
  • If a question has no visible printed number, set source_question_number to
    null — do NOT invent a number to fill the sequence.
  • Do not renumber questions based on their position in your output array.
- Identify the correct answer from the answer key or context
- Preserve the original wording as closely as possible
- If no passage, set passage_text to null
- For a single question, return a questions array with one element
- If a question is accompanied by a table, chart, graph, or figure, populate stimulus_assets for that question with one entry per distinct visual element. If there are no visual elements, set stimulus_assets to []
- For tables: extract headers and rows into structured_data. For charts/graphs: extract axis labels and data series into structured_data. For figures: provide a text description
- Output ONLY valid JSON, no markdown fences"""


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
