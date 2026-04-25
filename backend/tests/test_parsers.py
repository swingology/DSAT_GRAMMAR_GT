import pytest
import os
import tempfile
from app.parsers.json_parser import extract_json_from_text, normalize_annotation
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
    assert "classification" not in result
    assert "question" not in result


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
    assert "unknown_key" not in result


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