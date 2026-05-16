"""GLM-OCR layout-detection prompt — identifies question/table/chart/figure regions
on a page image and returns structured bounding boxes."""

LAYOUT_SYSTEM_PROMPT = """You are a document layout analyzer. Given one page image from a standardized test, identify every distinct region and return a JSON array.

Region types:
- "question_block": a complete question (stem, passage if any, answer choices)
- "table": a data table with rows and columns
- "chart": a bar chart, line graph, pie chart, or other data visualization
- "figure": an image, diagram, or illustration that is not a chart

For each region return:
- "type": one of the region types above
- "label": the question number (e.g. "Q3", "Q27") or a descriptive label (e.g. "Table 1", "Chart A")
- "bbox": {"x": float, "y": float, "w": float, "h": float}
  - x, y: top-left corner, normalized to 0.0–1.0 relative to image width/height
  - w, h: width and height, normalized to 0.0–1.0
  - all values are fractions of the full page dimensions (0.0 = left/top edge, 1.0 = right/bottom edge)

Important:
- Every question on the page should have a question_block region
- Tables, charts, and figures that belong to a question should have their own separate regions
- Do NOT overlap regions — each pixel belongs to at most one region
- Regions should cover the full visual extent of the content (including answer choices for question blocks)
- If a question spans a passage and its stem/choices, include the passage in the question_block

Return ONLY a valid JSON array. No commentary, no markdown fences, no trailing text."""


def build_layout_prompt(source_metadata: dict | None = None) -> tuple[str, str]:
    """Return (system, user) prompt pair for a single-page layout-detection call.

    source_metadata: optional dict with exam/module info to help the model
        understand context (e.g. {"source_exam_code": "PT1", "source_subject_code": "verbal"}).
    """
    source_hints = ""
    if source_metadata:
        hints = [f"{k}: {v}" for k, v in source_metadata.items() if v]
        source_hints = "\nSource context:\n" + "\n".join(hints) if hints else ""

    user = (
        f"Analyze the layout of this test page. Identify all question blocks, "
        f"tables, charts, and figures with their bounding boxes.{source_hints}"
    )
    return LAYOUT_SYSTEM_PROMPT, user