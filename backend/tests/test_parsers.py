import pytest
import os
import tempfile
from app.parsers.json_parser import (
    extract_json_from_text,
    normalize_annotation,
    canonicalize_annotation,
)
from app.parsers.pdf_parser import parse_pdf
from app.parsers.image_parser import parse_image
from app.parsers.markdown_parser import parse_markdown


# --- JSON Parser ---

def test_extract_json_from_clean_text():
    text = '{"question_text": "Which choice?", "options": []}'
    result = extract_json_from_text(text)
    assert result["question_text"] == "Which choice?"


def test_extract_json_from_markdown_fence():
    text = '```json\n{"question_text": "test"}\n```'
    result = extract_json_from_text(text)
    assert result["question_text"] == "test"


def test_extract_json_from_mixed_text():
    text = 'Here is the result:\n```json\n{"key": "value"}\n```\nDone.'
    result = extract_json_from_text(text)
    assert result["key"] == "value"


def test_extract_json_raises_on_invalid():
    with pytest.raises(ValueError, match="No valid JSON found"):
        extract_json_from_text("no json here at all")


def test_extract_json_from_bracket_search():
    text = 'Some prefix text {"nested": {"key": 1}} some suffix'
    result = extract_json_from_text(text)
    assert result["nested"]["key"] == 1


def test_extract_json_from_kimi_single_quotes_and_bare_keys():
    text = """
    Here is the extracted JSON:
    {
      question_text: 'Which choice completes the text?',
      options: [
        {"label": "A", "text": "one"},
        {"label": "B", "text": "two"},
        {"label": "C", "text": "three"},
        {"label": "D", "text": "four"},
      ],
      correct_option_label: 'C',
    }
    """
    result = extract_json_from_text(text, provider_name="ollama", model_name="deepseek-v4-pro:cloud")
    assert result["question_text"] == "Which choice completes the text?"
    assert result["correct_option_label"] == "C"
    assert len(result["options"]) == 4


def test_extract_json_strips_thinking_tags():
    text = "<thinking>Step-by-step reasoning here.</thinking>\n{\"question_text\": \"Q?\"}"
    result = extract_json_from_text(text, provider_name="anthropic", model_name="claude-sonnet")
    assert result["question_text"] == "Q?"


def test_extract_json_universal_repair_fallback_for_non_ollama():
    """Non-Ollama providers get the repair path as a last-resort fallback."""
    text = "{question_text: 'Which choice?', correct_option_label: 'A',}"
    result = extract_json_from_text(text, provider_name="anthropic", model_name="claude-sonnet")
    assert result["question_text"] == "Which choice?"


def test_extract_json_raises_with_context_on_failure():
    with pytest.raises(ValueError) as exc_info:
        extract_json_from_text("no json here", provider_name="openai", model_name="gpt-4o")
    msg = str(exc_info.value)
    assert "provider=" in msg
    assert "model=" in msg
    assert "preview=" in msg


def test_extract_json_from_kimi_think_block_and_js_fence():
    text = """
    <think>Need to structure this carefully.</think>
    ```javascript
    {
      question_text: "Sample question",
      options: [
        {label: "A", text: "alpha"},
        {label: "B", text: "beta"},
        {label: "C", text: "gamma"},
        {label: "D", text: "delta"}
      ],
      correct_option_label: "A"
    }
    ```
    """
    result = extract_json_from_text(text, provider_name="ollama", model_name="deepseek-v4-pro:cloud")
    assert result["question_text"] == "Sample question"
    assert result["options"][0]["label"] == "A"


# --- Annotation Normalizer ---

def test_normalize_annotation_flat_passthrough():
    data = {"grammar_focus_key": "subject_verb_agreement", "explanation_short": "Good."}
    assert normalize_annotation(data) == data


def test_normalize_annotation_flattens_nested_keys():
    data = {
        "classification": {
            "grammar_focus_key": "subject_verb_agreement",
            "grammar_role_key": "error_identification",
        },
        "question": {
            "explanation_short": "Because A.",
            "explanation_full": "Long explanation.",
        },
        "annotation_confidence": 0.9,
        "needs_human_review": False,
    }
    result = normalize_annotation(data)
    assert result["grammar_focus_key"] == "subject_verb_agreement"
    assert result["grammar_role_key"] == "error_identification"
    assert result["explanation_short"] == "Because A."
    assert result["explanation_full"] == "Long explanation."
    assert result["annotation_confidence"] == 0.9
    assert result["needs_human_review"] is False
    assert result["classification"]["grammar_focus_key"] == "subject_verb_agreement"
    assert result["question"]["explanation_short"] == "Because A."


def test_normalize_annotation_top_level_wins_over_nested():
    data = {
        "explanation_short": "Top-level wins.",
        "nested": {"explanation_short": "Should be ignored."},
    }
    result = normalize_annotation(data)
    assert result["explanation_short"] == "Top-level wins."


def test_normalize_annotation_ignores_unknown_nested_keys():
    data = {"wrapper": {"unknown_key": "value", "explanation_short": "Kept."}}
    result = normalize_annotation(data)
    assert result["explanation_short"] == "Kept."
    assert result["wrapper"]["unknown_key"] == "value"


def test_normalize_annotation_promotes_reading_keys_from_classification():
    # Reproduces the real-world case where the LLM nests reading fields
    # under a 'classification' key instead of returning them flat.
    data = {
        "stem_type_key": "choose_words_in_context",
        "grammar_focus_key": None,
        "grammar_role_key": None,
        "classification": {
            "question_family_key": "craft_and_structure",
            "skill_family_key": "words_in_context",
            "reading_focus_key": "precision_fit",
            "difficulty_overall": "low",
            "reasoning_trap_key": "topical_relevance_without_logical_connection",
        },
    }
    result = normalize_annotation(data)
    assert result["question_family_key"] == "craft_and_structure"
    assert result["skill_family_key"] == "words_in_context"
    assert result["reading_focus_key"] == "precision_fit"
    assert result["difficulty_overall"] == "low"
    assert result["reasoning_trap_key"] == "topical_relevance_without_logical_connection"
    # original nested structure preserved
    assert result["classification"]["question_family_key"] == "craft_and_structure"


def test_normalize_annotation_converts_skill_family_display_name():
    # When the LLM outputs 'skill_family' as a human-readable name instead of
    # snake_case 'skill_family_key', normalize_annotation should convert it.
    data = {
        "classification": {
            "question_family_key": "craft_and_structure",
            "skill_family": "Words in Context",  # display name, not snake_case key
            "reading_focus_key": "precision_fit",
        },
    }
    result = normalize_annotation(data)
    assert result["skill_family_key"] == "words_in_context"
    assert result["question_family_key"] == "craft_and_structure"
    assert result["reading_focus_key"] == "precision_fit"


def test_normalize_annotation_skill_family_key_wins_over_display_name():
    # If skill_family_key already exists at top level, display-name conversion
    # should not overwrite it.
    data = {
        "skill_family_key": "inferences",
        "classification": {
            "skill_family": "Words in Context",
        },
    }
    result = normalize_annotation(data)
    assert result["skill_family_key"] == "inferences"


# --- canonicalize_annotation (deterministic shape reconciliation) ---

def test_canonicalize_promotes_absent_top_level_from_nested():
    # Live failure shape: classification has the value, top level lacks it.
    raw = {"classification": {"question_family_key": "craft_and_structure"}}
    result = canonicalize_annotation(raw)
    assert result["question_family_key"] == "craft_and_structure"
    assert "question_family_key" in result["_annotation_quality"]["promoted_fields"]


def test_canonicalize_repairs_null_top_level_from_nested():
    # The exact gap the old normalize_annotation could not close: top-level null
    # blocks promotion. canonicalize must repair it.
    raw = {
        "question_family_key": None,
        "difficulty_overall": None,
        "classification": {
            "question_family_key": "craft_and_structure",
            "difficulty_overall": "medium",
            "syntactic_trap_key": "nearest_noun_attraction",
        },
    }
    result = canonicalize_annotation(raw)
    assert result["question_family_key"] == "craft_and_structure"
    assert result["difficulty_overall"] == "medium"
    assert result["syntactic_trap_key"] == "nearest_noun_attraction"
    repaired = result["_annotation_quality"]["repaired_from_nested"]
    assert "question_family_key" in repaired
    assert "difficulty_overall" in repaired


def test_canonicalize_treats_none_string_as_empty():
    raw = {
        "syntactic_trap_key": "none",
        "classification": {"syntactic_trap_key": "long_distance_dependency"},
    }
    result = canonicalize_annotation(raw)
    assert result["syntactic_trap_key"] == "long_distance_dependency"


def test_canonicalize_conflict_keeps_top_level_and_flags_review():
    # Multi-LLM danger case: top-level and nested disagree, both non-empty.
    raw = {
        "question_family_key": "conventions_grammar",
        "classification": {"question_family_key": "craft_and_structure"},
    }
    result = canonicalize_annotation(raw)
    assert result["question_family_key"] == "conventions_grammar"  # top-level wins
    assert result["needs_human_review"] is True
    conflicts = result["_annotation_quality"]["conflicts"]
    assert conflicts[0]["field"] == "question_family_key"
    assert conflicts[0]["kept_top_level"] == "conventions_grammar"
    assert conflicts[0]["nested_value"] == "craft_and_structure"


def test_canonicalize_normalizes_reading_skill_family_alias():
    raw = {"reading_skill_family_key": "inferences"}
    result = canonicalize_annotation(raw)
    assert result["skill_family_key"] == "inferences"


def test_canonicalize_converts_skill_family_display_name_from_nested():
    raw = {"classification": {"skill_family": "Words in Context"}}
    result = canonicalize_annotation(raw)
    assert result["skill_family_key"] == "words_in_context"


def test_canonicalize_passage_tokens_soft_fallback():
    raw = {"classification": {"passage_tokens": [{"t": "x"}]}}
    result = canonicalize_annotation(raw)
    assert result["passage_tokens"] == [{"t": "x"}]


def test_canonicalize_noop_on_flat_complete_annotation():
    raw = {"question_family_key": "conventions_grammar", "grammar_role_key": "agreement"}
    result = canonicalize_annotation(raw)
    assert result["question_family_key"] == "conventions_grammar"
    assert "_annotation_quality" not in result


# --- PDF Parser ---

def test_parse_pdf_returns_pages():
    """Test with a real small PDF or skip if no PDF available."""
    sample = os.path.join(
        os.path.dirname(__file__), "..", "..",
        "sat-practice-test-4-digital sec01 mod01.pdf"
    )
    if not os.path.exists(sample):
        pytest.skip("No sample PDF available")
    result = parse_pdf(sample)
    assert "pages" in result
    assert len(result["pages"]) > 0
    assert "text" in result["pages"][0]


def test_parse_pdf_page_structure():
    """Each page should have text and page_number."""
    sample = os.path.join(
        os.path.dirname(__file__), "..", "..",
        "sat-practice-test-4-digital sec01 mod01.pdf"
    )
    if not os.path.exists(sample):
        pytest.skip("No sample PDF available")
    result = parse_pdf(sample)
    page = result["pages"][0]
    assert "page_number" in page
    assert "text" in page
    assert isinstance(page["text"], str)


def test_parse_pdf_includes_full_page_render_for_text_pdf(tmp_path):
    import fitz

    pdf_path = tmp_path / "text_with_vector.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Question 1")
    page.draw_rect(fitz.Rect(72, 100, 200, 160), color=(0, 0, 0))
    doc.save(pdf_path)
    doc.close()

    result = parse_pdf(str(pdf_path))
    page_data = result["pages"][0]

    assert page_data["text"].strip()
    assert page_data["render"]["rendered"] is True
    assert page_data["render"]["ext"] == "png"
    assert len(page_data["render"]["b64"]) > 0


# --- Image Parser ---

def test_image_parser_returns_b64():
    """Create a tiny test image and verify base64 output."""
    from PIL import Image
    import io
    img = Image.new("RGB", (10, 10), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(buf.getvalue())
        f.flush()
        result = parse_image(f.name)
    assert "b64" in result
    assert "mime_type" in result
    assert result["mime_type"] == "image/png"
    assert len(result["b64"]) > 0


# --- Markdown Parser ---

def test_markdown_parser_plain():
    result = parse_markdown("# Title\n\nSome question text here.")
    assert result["text"] == "# Title\n\nSome question text here."
    assert result["front_matter"] == {}


def test_markdown_parser_with_front_matter():
    md = "---\nsource_name: PrepPros\nsource_url: https://example.com\n---\n# Question\n\nText here."
    result = parse_markdown(md)
    assert result["front_matter"]["source_name"] == "PrepPros"
    assert "Question" in result["text"]
